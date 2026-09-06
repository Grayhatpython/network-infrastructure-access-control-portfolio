-- MySQL HR/RADIUS policy extension

CREATE TABLE dept_vlan_map
(
    dept_code    VARCHAR(10) NOT NULL,
    group_name   VARCHAR(64) NOT NULL,
    vlan_id      SMALLINT UNSIGNED NOT NULL,
    description  VARCHAR(100) NULL,
    enabled      TINYINT(1) NOT NULL DEFAULT 1,

    CONSTRAINT pk_dept_vlan_map PRIMARY KEY (dept_code),
    CONSTRAINT uq_dept_vlan_group UNIQUE (group_name),
    CONSTRAINT ck_dept_vlan_id CHECK (vlan_id BETWEEN 1 AND 4094)
);

CREATE TABLE hr_employee_stage
(
    username          VARCHAR(64) NOT NULL,
    emp_name          VARCHAR(100) NOT NULL,
    nt_password_hash  CHAR(32) NOT NULL,
    dept_code         VARCHAR(10) NOT NULL,
    active_yn         CHAR(1) NOT NULL,
    hr_updated_at     DATETIME(6) NULL,
    synced_at         TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT pk_hr_employee_stage PRIMARY KEY (username),
    CONSTRAINT ck_hr_employee_active CHECK (active_yn IN ('Y', 'N')),
    INDEX idx_hr_stage_dept (dept_code)
);

CREATE TABLE hr_managed_user
(
    username         VARCHAR(64) NOT NULL,
    last_dept_code   VARCHAR(10) NOT NULL,
    last_group_name  VARCHAR(64) NOT NULL,
    last_vlan_id     SMALLINT UNSIGNED NULL,
    last_active_yn   CHAR(1) NOT NULL DEFAULT 'Y',
    first_synced_at  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_seen_at     TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_applied_at  TIMESTAMP NULL,

    CONSTRAINT pk_hr_managed_user PRIMARY KEY (username),
    CONSTRAINT ck_hr_managed_user_active
        CHECK (last_active_yn IN ('Y', 'N'))
);

-- Event table is intentionally left for the next implementation milestone.
