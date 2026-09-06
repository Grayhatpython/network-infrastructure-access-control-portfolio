# 15. 공개 코드의 범위와 최신 랩의 차이

[README](../README.md) · [프로젝트 상태](../PROJECT_STATUS.md)

이 문서는 현재 Repository에 포함된 실행 파일과 최신 랩에서 검증한 기능의 범위를 구분하기 위해 작성했습니다.

## 파일별 실제 범위

| 파일·영역 | 공개 파일에서 확인한 내용 | 포함되지 않은 범위 |
|---|---|---|
| `scripts/sync-dhcp-from-db.py` | Scope·Pool·Reservation 조회, 설정 생성·문법 검사, 비교·백업·교체·재시작, 복원 시도 | 최신 Event 기반 정리 함수와 장애 복구 전체 |
| `scripts/sync-hr-to-radius.py` | HR 조회·검증, 매핑, 변경 분류, Stage 갱신; 일부 정책 처리 함수 정의 | Event Dispatcher, 최신 단계 함수의 통합 실행 |
| `sql/mysql/01_dhcp_ipam_schema.sql` | DHCP/IPAM 기본 4개 테이블 | 최신 랩 DDL 전체와 완전한 설치 마이그레이션 |
| `sql/mysql/02_hr_radius_schema.sql` | 부서 매핑, Stage, Applied 테이블 | `hr_network_event`, `hr_network_action_log` DDL |
| `sql/mysql/03_triggers.sql` | Reservation DELETE 시 Pool 복귀 Trigger | 전체 DHCPACK 파서·최초 예약 Trigger |
| `sql/oracle/01_hr_schema.sql` | HR 테이블·View·갱신 Trigger의 공개 스냅샷 | 실제 계정·권한·데이터 전체 |
| `systemd/dhcp-db-sync.*` | DHCP 동기화 unit | HR Event Worker 운영 |
| `systemd/hr-radius-sync.*.example` | HR 실행 unit 예시 | 전체 상태 흐름 자동화 완료의 증거 |

## HR `main()`의 활성 경로

```text
load_config
→ fetch_hr_accounts
→ validate_hr_accounts
→ connect_mysql
→ load_vlan_mapping / load_managed_users
→ detect_changes / 로그
→ refresh_stage / commit
```

이 실행으로 스위치 CoA, 최신 Event 기록, OLD 예약 자동 정리, 최종 Applied 확정까지 수행되지는 않습니다. 랩에서 별도 호출로 검증한 최신 함수를 확보해 정리하는 작업이 남아 있습니다.

## 재현 범위

현재 저장소는 **설계·구현 과정과 일부 실행 스냅샷을 공유하는 포트폴리오**입니다. 저장소를 복제하고 한 명령으로 전체 랩을 구축하는 배포 패키지가 아닙니다. FreeRADIUS 기본 SQL 스키마, 장비 전체 설정, 최신 Event 마이그레이션, 전체 수집 Trigger, 실제 환경 설정은 별도로 준비해야 합니다.

## 공개 DHCP 스크립트에서 추가 점검할 항목

아래는 현재 공개 파일을 읽고 정리한 후속 점검 사항이며 최신 랩 서버에서 동일 문제가 재현됐다고 주장하지 않습니다.

1. Reservation SELECT는 Scope의 `enabled`까지 확인하지만, 마지막 `APPLIED` UPDATE는 같은 Scope 조건으로 제한하지 않습니다. 생성에 포함된 대상만 완료 표시하는지 점검해야 합니다.
2. 후보 설정과 기존 파일이 같으면 조기 종료하므로, DB에 남은 적용 상태와 파일의 정합성을 별도로 맞출 필요가 있는지 검토해야 합니다.
3. Scope·Pool·Reservation을 각각 조회하므로 여러 변경이 동시에 발생할 때 한 정책 스냅샷으로 읽히는지 검증해야 합니다.
4. 수동 실행과 timer 실행이 겹칠 때의 프로세스 잠금, 설정 교체와 DB 상태 갱신 사이의 실패 처리를 검증해야 합니다.
5. 백업 복원 후 재시작 성공까지 강하게 확인하는 복구 조건이 필요합니다.

## 다음 코드 공개 때 필요한 것

최신 서버의 마스킹된 스크립트·DDL·관련 Trigger를 같은 버전으로 묶고, State별 실행 순서와 성공·실패 결과를 함께 공개합니다. 그 시점에 이 문서의 미포함 항목을 실제 파일과 대조해 갱신합니다.
