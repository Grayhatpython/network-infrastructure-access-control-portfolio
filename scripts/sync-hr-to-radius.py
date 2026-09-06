#!/opt/hr-radius-sync/venv/bin/python

# PORTFOLIO SNAPSHOT (WIP)
# Current stage: Desired/Applied state comparison + change detection only.
# Event journal, automatic CoA and DHCP cleanup are intentionally not enabled yet.

# INI 형태의 설정 파일을 읽기 위한 표준 라이브러리
import configparser

# 실행 과정과 에러를 systemd journal에 남기기 위한 라이브러리
import logging

# NT Hash가 32자리 16진수인지 검사하기 위해 사용
import re

# Oracle Database 연결용
import oracledb

# MySQL 연결용
import mysql.connector


# ---------------------------------------------------------
# 기본 설정
# ---------------------------------------------------------

# Oracle / MySQL ID, Password 등이 들어 있는 설정파일
CONFIG_FILE = "/etc/hr-radius-sync.ini"


# Python logging 설정
#
# systemd로 실행하면 이 내용은 journalctl에서 확인할 수 있다.
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s"
)


# logging.getLogger()로 현재 프로그램용 Logger를 생성
logger = logging.getLogger(__name__)


# ---------------------------------------------------------
# 설정파일 읽기
# ---------------------------------------------------------

def load_config():
    """
    /etc/hr-radius-sync.ini 파일을 읽어서 반환한다.
    """

    # ConfigParser 객체 생성
    config = configparser.ConfigParser()

    # 실제 파일 읽기
    read_files = config.read(CONFIG_FILE)

    # 파일을 읽지 못했다면 작업을 중단
    if not read_files:
        raise RuntimeError(
            f"Cannot read configuration file: {CONFIG_FILE}"
        )

    # 필요한 두 section이 있는지 검사
    if "oracle" not in config:
        raise RuntimeError(
            "[oracle] section is missing"
        )

    if "mysql" not in config:
        raise RuntimeError(
            "[mysql] section is missing"
        )

    return config


# ---------------------------------------------------------
# Oracle HR 정보 가져오기
# ---------------------------------------------------------

def fetch_hr_accounts(config):
    """
    Oracle의 HR_APP.V_RADIUS_ACCOUNT View에서
    RADIUS에 필요한 직원정보만 읽는다.
    """

    logger.info(
        "Connecting to Oracle HR database..."
    )

    # Oracle 접속
    connection = oracledb.connect(
        user=config["oracle"]["user"],
        password=config["oracle"]["password"],
        dsn=config["oracle"]["dsn"],
    )

    try:

        # SQL을 실행할 Cursor 생성
        cursor = connection.cursor()

        try:

            cursor.execute(
                """
                SELECT
                    emp_id,
                    emp_name,
                    nt_password_hash,
                    dept_code,
                    active_yn,
                    updated_at

                FROM HR_APP.V_RADIUS_ACCOUNT

                ORDER BY emp_id
                """
            )

            # SELECT 결과 전체를 Python 메모리로 가져옴
            rows = cursor.fetchall()

        finally:

            # Cursor는 사용이 끝났으므로 닫음
            cursor.close()

    finally:

        # Oracle 연결도 반드시 닫음
        connection.close()

    # Oracle 장애나 잘못된 View 때문에 0명이 반환되는 경우
    #
    # 실수로 전체 RADIUS 계정을 삭제하거나 변경하는 상황을
    # 방지하기 위해 작업을 중단한다.
    if not rows:
        raise RuntimeError(
            "Oracle returned zero HR accounts. "
            "Synchronization aborted for safety."
        )

    logger.info(
        "Fetched %d HR accounts from Oracle.",
        len(rows),
    )

    return rows


# ---------------------------------------------------------
# Oracle 데이터 자체 검증
# ---------------------------------------------------------

def validate_hr_accounts(rows):
    """
    Oracle에서 가져온 데이터가 실제 RADIUS에 넣어도 되는
    정상적인 데이터인지 검사한다.
    """

    # 동일 username이 중복되는지 검사하기 위한 set
    seen_usernames = set()

    for row in rows:

        (
            username,
            emp_name,
            nt_password_hash,
            dept_code,
            active_yn,
            updated_at,
        ) = row

        # 앞뒤 공백 제거
        username = username.strip()

        # username이 비어 있으면 절대 계정을 만들면 안 됨
        if not username:
            raise ValueError(
                "Empty employee username found."
            )

        # 같은 username이 두 번 나타나는지도 검사
        if username in seen_usernames:
            raise ValueError(
                f"Duplicate username found: {username}"
            )

        seen_usernames.add(username)

        # 활성 상태는 Y / N 두 값만 허용
        if active_yn not in ("Y", "N"):
            raise ValueError(
                f"Invalid active_yn for {username}: {active_yn}"
            )

        # 활성 계정만 실제 인증정보를 필요로 한다.
        if active_yn == "Y":

            # NT Hash는 정확히 32자리 16진수여야 함
            if not re.fullmatch(
                r"[0-9A-Fa-f]{32}",
                nt_password_hash.strip(),
            ):

                raise ValueError(
                    f"Invalid NT password hash for {username}"
                )

            if not dept_code:
                raise ValueError(
                    f"Missing department for {username}"
                )


# ---------------------------------------------------------
# MySQL 연결
# ---------------------------------------------------------

def connect_mysql(config):
    """
    FreeRADIUS radius DB에 연결한다.
    """

    return mysql.connector.connect(
        host=config["mysql"]["host"],
        port=config["mysql"].getint("port"),
        user=config["mysql"]["user"],
        password=config["mysql"]["password"],
        database=config["mysql"]["database"],

        # 우리가 직접 COMMIT / ROLLBACK 할 것이므로
        # autocommit은 끈다.
        autocommit=False,
    )


# ---------------------------------------------------------
# 부서 → VLAN 정책 가져오기
# ---------------------------------------------------------

def load_vlan_mapping(mysql_connection):
    """
    dept_vlan_map을 Dictionary 형태로 가져온다.

    결과 예:

    {
        "200": {
            "group_name": "VLAN_200",
            "vlan_id": 200
        }
    }
    """

    cursor = mysql_connection.cursor()

    try:

        cursor.execute(
            """
            SELECT
                dept_code,
                group_name,
                vlan_id

            FROM dept_vlan_map

            WHERE enabled = 1
            """
        )

        rows = cursor.fetchall()

    finally:

        cursor.close()

    mapping = {}

    for dept_code, group_name, vlan_id in rows:

        mapping[dept_code] = {
            "group_name": group_name,
            "vlan_id": int(vlan_id),
        }

    if not mapping:
        raise RuntimeError(
            "dept_vlan_map contains no enabled policies."
        )

    return mapping


# ---------------------------------------------------------
# radgroupreply VLAN 정책 동기화
# ---------------------------------------------------------

def sync_group_reply(
    mysql_connection,
    vlan_mapping,
):
    """
    dept_vlan_map을 기준으로 FreeRADIUS radgroupreply를 구성한다.
    """

    cursor = mysql_connection.cursor()

    try:

        for dept_code, policy in vlan_mapping.items():

            group_name = policy["group_name"]
            vlan_id = policy["vlan_id"]

            # 이 프로그램이 관리하는 VLAN 관련 Attribute만 제거
            #
            # 다른 RADIUS 정책 Attribute는 건드리지 않는다.
            cursor.execute(
                """
                DELETE FROM radgroupreply

                WHERE groupname = %s

                  AND attribute IN
                  (
                      'Tunnel-Type',
                      'Tunnel-Medium-Type',
                      'Tunnel-Private-Group-Id'
                  )
                """,
                (group_name,),
            )

            # Tunnel-Type = VLAN
            cursor.execute(
                """
                INSERT INTO radgroupreply
                (
                    groupname,
                    attribute,
                    op,
                    value
                )
                VALUES
                (
                    %s,
                    'Tunnel-Type',
                    ':=',
                    'VLAN'
                )
                """,
                (group_name,),
            )

            # Ethernet VLAN
            cursor.execute(
                """
                INSERT INTO radgroupreply
                (
                    groupname,
                    attribute,
                    op,
                    value
                )
                VALUES
                (
                    %s,
                    'Tunnel-Medium-Type',
                    ':=',
                    'IEEE-802'
                )
                """,
                (group_name,),
            )

            # 실제 VLAN 번호
            cursor.execute(
                """
                INSERT INTO radgroupreply
                (
                    groupname,
                    attribute,
                    op,
                    value
                )
                VALUES
                (
                    %s,
                    'Tunnel-Private-Group-Id',
                    ':=',
                    %s
                )
                """,
                (
                    group_name,
                    str(vlan_id),
                ),
            )

    finally:

        cursor.close()


# ---------------------------------------------------------
# Stage Table 갱신
# ---------------------------------------------------------

def refresh_stage(
    mysql_connection,
    rows,
):
    """
    책의 tmp_employee와 동일한 개념이다.

    매 실행마다 Oracle Snapshot을 stage table에 새로 적재한다.
    """

    cursor = mysql_connection.cursor()

    try:

        # 이전 Snapshot 제거
        cursor.execute(
            "DELETE FROM hr_employee_stage"
        )

        insert_sql = """
            INSERT INTO hr_employee_stage
            (
                username,
                emp_name,
                nt_password_hash,
                dept_code,
                active_yn,
                hr_updated_at
            )
            VALUES
            (
                %s,
                %s,
                %s,
                %s,
                %s,
                %s
            )
        """

        values = []

        for row in rows:

            (
                username,
                emp_name,
                nt_password_hash,
                dept_code,
                active_yn,
                updated_at,
            ) = row

            values.append(
                (
                    username.strip(),
                    emp_name,
                    nt_password_hash.strip().upper(),
                    dept_code,
                    active_yn,
                    updated_at,
                )
            )

        # 여러 직원 데이터를 한 번에 INSERT
        cursor.executemany(
            insert_sql,
            values,
        )

    finally:

        cursor.close()


# ---------------------------------------------------------
# 단일 사용자 활성화
# ---------------------------------------------------------

def apply_radius_user(
    mysql_connection,
    username,
    nt_hash,
    group_name,
):
    """
    활성 직원 한 명의 FreeRADIUS 인증/그룹 정책만 반영한다.
    """

    cursor = mysql_connection.cursor()

    try:

        # -------------------------------------------------
        # 계정 충돌 방지
        # -------------------------------------------------
        #
        # HR가 한 번도 관리하지 않은 사용자인데
        # 이미 radcheck에 같은 username이 존재하면
        # 수동 계정을 덮어쓰면 안 된다.

        cursor.execute(
            """
            SELECT 1

            FROM hr_managed_user

            WHERE username = %s
            """,
            (username,),
        )

        managed = cursor.fetchone() is not None

        if not managed:

            cursor.execute(
                """
                SELECT 1

                FROM radcheck

                WHERE username = %s

                LIMIT 1
                """,
                (username,),
            )

            if cursor.fetchone():

                raise RuntimeError(
                    f"RADIUS username collision: {username}"
                )

        # -------------------------------------------------
        # Password Attribute 갱신
        # -------------------------------------------------

        # 예전에 Cleartext-Password 방식으로 만들어진 행이나
        # 이전 NT-Password를 제거
        cursor.execute(
            """
            DELETE FROM radcheck

            WHERE username = %s

              AND attribute IN
                  (
                      'NT-Password',
                      'Cleartext-Password'
                  )
            """,
            (username,),
        )

        # 현재 NT Hash 등록
        cursor.execute(
            """
            INSERT INTO radcheck
            (
                username,
                attribute,
                op,
                value
            )
            VALUES
            (
                %s,
                'NT-Password',
                ':=',
                %s
            )
            """,
            (
                username,
                nt_hash.upper(),
            ),
        )

        # -------------------------------------------------
        # 기존 HR VLAN 그룹 제거
        # -------------------------------------------------

        # 모든 그룹을 지우지 않고
        # dept_vlan_map에 등록된 VLAN 그룹만 제거한다.
        #
        # 따라서 다른 수동 RADIUS 그룹이 있다면 보존된다.
        cursor.execute(
            """
            DELETE rug

            FROM radusergroup rug

            INNER JOIN dept_vlan_map dvm
                    ON rug.groupname = dvm.group_name

            WHERE rug.username = %s
            """,
            (username,),
        )

        # 현재 부서에 맞는 그룹 하나 등록
        cursor.execute(
            """
            INSERT INTO radusergroup
            (
                username,
                groupname,
                priority
            )
            VALUES
            (
                %s,
                %s,
                1
            )
            """,
            (
                username,
                group_name,
            ),
        )

    finally:

        cursor.close()



# ---------------------------------------------------------
# Applied State 관리
# ---------------------------------------------------------

def mark_user_applied(
    mysql_connection,
    username,
    dept_code,
    group_name,
    vlan_id,
    active_yn="Y",
):
    """
    외부 네트워크 작업까지 성공적으로 완료된 후에만
    hr_managed_user의 Applied State를 확정한다.

    현재 change-detection 단계에서는 아직 호출하지 않는다.
    """

    cursor = mysql_connection.cursor()

    try:
        cursor.execute(
            """
            INSERT INTO hr_managed_user
            (
                username,
                last_dept_code,
                last_group_name,
                last_vlan_id,
                last_active_yn,
                last_applied_at
            )
            VALUES
            (
                %s,
                %s,
                %s,
                %s,
                %s,
                CURRENT_TIMESTAMP
            )

            ON DUPLICATE KEY UPDATE
                last_dept_code = %s,
                last_group_name = %s,
                last_vlan_id = %s,
                last_active_yn = %s,
                last_seen_at = CURRENT_TIMESTAMP,
                last_applied_at = CURRENT_TIMESTAMP
            """,
            (
                username,
                dept_code,
                group_name,
                vlan_id,
                active_yn,
                dept_code,
                group_name,
                vlan_id,
                active_yn,
            ),
        )
    finally:
        cursor.close()


def load_managed_users(mysql_connection):
    """
    마지막으로 성공적으로 적용된 HR 사용자 상태를 읽는다.
    username을 key로 하는 dict를 반환한다.
    """

    cursor = mysql_connection.cursor()

    try:
        cursor.execute(
            """
            SELECT
                username,
                last_dept_code,
                last_group_name,
                last_vlan_id,
                last_active_yn,
                last_applied_at
            FROM hr_managed_user
            """
        )
        rows = cursor.fetchall()
    finally:
        cursor.close()

    managed = {}

    for (
        username,
        last_dept_code,
        last_group_name,
        last_vlan_id,
        last_active_yn,
        last_applied_at,
    ) in rows:
        managed[username] = {
            "dept_code": last_dept_code,
            "group_name": last_group_name,
            "vlan_id": int(last_vlan_id) if last_vlan_id is not None else None,
            "active_yn": last_active_yn,
            "last_applied_at": last_applied_at,
        }

    return managed


def detect_changes(rows, vlan_mapping, managed_users):
    """
    Oracle Desired State와 마지막 Applied State를 비교해
    네트워크 변경 계획을 만든다.

    이 함수는 실제 RADIUS/Switch/DHCP를 변경하지 않는다.
    """

    changes = []

    for row in rows:
        (
            username,
            emp_name,
            nt_hash,
            dept_code,
            active_yn,
            updated_at,
        ) = row

        username = username.strip()
        old = managed_users.get(username)

        if active_yn == "N":
            if old is not None and old["active_yn"] == "Y":
                changes.append(
                    {
                        "type": "DEACTIVATE",
                        "username": username,
                        "old": old,
                        "new": None,
                        "hr_updated_at": updated_at,
                    }
                )
            continue

        if dept_code not in vlan_mapping:
            raise RuntimeError(
                f"No enabled VLAN mapping for department "
                f"{dept_code} (user={username})"
            )

        policy = vlan_mapping[dept_code]

        new = {
            "dept_code": dept_code,
            "group_name": policy["group_name"],
            "vlan_id": policy["vlan_id"],
            "active_yn": "Y",
        }

        if old is None:
            changes.append(
                {
                    "type": "NEW_USER",
                    "username": username,
                    "old": None,
                    "new": new,
                    "hr_updated_at": updated_at,
                }
            )
            continue

        if old["active_yn"] == "N":
            changes.append(
                {
                    "type": "REACTIVATE",
                    "username": username,
                    "old": old,
                    "new": new,
                    "hr_updated_at": updated_at,
                }
            )
            continue

        if old["dept_code"] != new["dept_code"]:
            changes.append(
                {
                    "type": "DEPT_MOVE",
                    "username": username,
                    "old": old,
                    "new": new,
                    "hr_updated_at": updated_at,
                }
            )
            continue

        if (
            old["group_name"] != new["group_name"]
            or old["vlan_id"] != new["vlan_id"]
        ):
            changes.append(
                {
                    "type": "POLICY_CHANGE",
                    "username": username,
                    "old": old,
                    "new": new,
                    "hr_updated_at": updated_at,
                }
            )

    oracle_usernames = {row[0].strip() for row in rows}

    for username, old in managed_users.items():
        if username not in oracle_usernames and old["active_yn"] == "Y":
            changes.append(
                {
                    "type": "HR_DELETE",
                    "username": username,
                    "old": old,
                    "new": None,
                    "hr_updated_at": None,
                }
            )

    return changes


# ---------------------------------------------------------
# 사용자 비활성화
# ---------------------------------------------------------

def deactivate_user(
    mysql_connection,
    username,
):
    """
    퇴직 또는 비활성 직원의 RADIUS 인증 권한을 제거한다.
    """

    cursor = mysql_connection.cursor()

    try:

        # HR가 관리한 계정인지 확인
        cursor.execute(
            """
            SELECT 1

            FROM hr_managed_user

            WHERE username = %s
            """,
            (username,),
        )

        # HR가 생성하지 않은 계정이면 건드리지 않음
        if cursor.fetchone() is None:
            return

        # 인증 Password 제거
        cursor.execute(
            """
            DELETE FROM radcheck

            WHERE username = %s

              AND attribute IN
                  (
                      'NT-Password',
                      'Cleartext-Password'
                  )
            """,
            (username,),
        )

        # HR VLAN group 제거
        cursor.execute(
            """
            DELETE rug

            FROM radusergroup rug

            INNER JOIN dept_vlan_map dvm
                    ON rug.groupname = dvm.group_name

            WHERE rug.username = %s
            """,
            (username,),
        )

    finally:

        cursor.close()


# ---------------------------------------------------------
# 전체 사용자 동기화
# ---------------------------------------------------------

def synchronize_accounts(
    mysql_connection,
    rows,
    vlan_mapping,
):
    """
    Oracle Snapshot을 실제 FreeRADIUS 계정정보에 반영한다.
    """

    active_count = 0
    inactive_count = 0

    for row in rows:

        (
            username,
            emp_name,
            nt_hash,
            dept_code,
            active_yn,
            updated_at,
        ) = row

        username = username.strip()

        # 활성 직원
        if active_yn == "Y":

            # 활성 직원인데 부서→VLAN 정책이 없으면
            # 임의 VLAN을 주지 않고 전체 Sync를 실패시킨다.
            if dept_code not in vlan_mapping:

                raise RuntimeError(
                    f"No VLAN mapping for department "
                    f"{dept_code} "
                    f"(user={username})"
                )

            policy = vlan_mapping[dept_code]

            activate_user(
                mysql_connection=mysql_connection,
                username=username,
                nt_hash=nt_hash.strip(),
                dept_code=dept_code,
                group_name=policy["group_name"],
            )

            active_count += 1

        # 비활성 직원
        else:

            deactivate_user(
                mysql_connection,
                username,
            )

            inactive_count += 1

    return active_count, inactive_count


# ---------------------------------------------------------
# main()
# ---------------------------------------------------------

def main():
    """
    현재 공개 스냅샷의 역할:
    Oracle Desired State와 hr_managed_user Applied State를 비교하고
    변경을 검출한다.

    현재 main()에서는 RADIUS / CoA / DHCP 변경을 실행하지 않는다.
    """

    logger.info("HR network change-detection scan started.")

    config = load_config()
    rows = fetch_hr_accounts(config)
    validate_hr_accounts(rows)

    mysql_connection = connect_mysql(config)

    try:
        vlan_mapping = load_vlan_mapping(mysql_connection)
        managed_users = load_managed_users(mysql_connection)

        changes = detect_changes(
            rows=rows,
            vlan_mapping=vlan_mapping,
            managed_users=managed_users,
        )

        for change in changes:
            logger.info(
                "Detected change: type=%s user=%s old=%s new=%s",
                change["type"],
                change["username"],
                change["old"],
                change["new"],
            )

        # Stage는 현재 Oracle Snapshot을 보여주는 Desired State 저장소다.
        # 실제 Applied State나 RADIUS 정책은 이 단계에서 변경하지 않는다.
        try:
            refresh_stage(mysql_connection, rows)
            mysql_connection.commit()
        except Exception:
            mysql_connection.rollback()
            raise

    finally:
        mysql_connection.close()

    logger.info(
        "HR network change-detection scan completed. detected=%d",
        len(changes),
    )


# 이 파일이 직접 실행되었을 때만 main() 실행
if __name__ == "__main__":
    main()