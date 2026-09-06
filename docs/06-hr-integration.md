# 06. Oracle HR 연동과 Desired / Applied

[README](../README.md) · [설계 결정](10-design-decisions.md)

## 별도 HR 서버

HR 서버 `172.16.10.11`에 Oracle Free Database를 구성하고, Auth 서버 `172.16.10.10`에서 `python-oracledb`로 `FREEPDB1` 원격 조회를 확인했습니다. 부서·직원을 `DEPARTMENT`와 `EMPLOYEE`로 나누고 `V_RADIUS_ACCOUNT`를 동기화의 조회 경계로 사용합니다.

```text
Oracle DEPARTMENT + EMPLOYEE
        ↓ V_RADIUS_ACCOUNT
Auth 서버 Python
        ↓ 입력 검증 / dept_vlan_map
MySQL hr_employee_stage
        ↓ 마지막 적용 상태와 비교
변경 감지 / Event
```

부서 코드와 VLAN 정책은 `dept_vlan_map`으로 연결합니다. 조직 데이터가 RADIUS Attribute까지 직접 관리하지 않도록 책임을 분리했습니다.

## 목표 상태와 실제 완료 상태

| 데이터 | 의미 | 갱신 시점 |
|---|---|---|
| `hr_employee_stage` | 현재 HR Snapshot, Desired | HR 조회·검증 후 |
| `hr_managed_user` | 마지막 성공 적용값, Applied | 네트워크 전환 및 정리 완료 후 |
| `hr_network_event` | 이번 변경의 OLD/NEW와 처리 상태 | 감지부터 `DONE`까지 |

VLAN21 → VLAN20 이동 중에는 Desired가 20이어도 Applied는 21을 유지합니다. 새 VLAN 적용과 DHCP 정리가 완료되면, 최종 조건을 재검증한 뒤 Applied 갱신과 Event `DONE`을 하나의 MySQL 트랜잭션으로 커밋합니다.

## 변경 감지와 처리 완료의 차이

공개 코드에는 `NEW_USER`, `REACTIVATE`, `DEPT_MOVE`, `POLICY_CHANGE`, `DEACTIVATE`, `HR_DELETE` 분류가 있습니다. 분류 함수가 있다는 사실만으로 각 이벤트의 네트워크 후처리를 완료한 것은 아닙니다. 최신 단계별 정상 경로 검증은 `DEPT_MOVE`를 기준으로 합니다.

## 공개 HR 스크립트

현재 [sync-hr-to-radius.py](../scripts/sync-hr-to-radius.py)의 `main()`은 HR 조회, 입력 검증, 정책 매핑·Applied 조회, 변경 로그, Stage 갱신까지 수행합니다. 파일에 일부 정책 처리 함수가 있어도 현재 `main()`이 전체 Event 처리·CoA·DHCP 정리·최종 완료를 호출하지는 않습니다.

최신 랩에서는 그 이후의 Event 단계별 함수까지 검증했으며, 최신 스크립트와 DDL을 정리해 공개하는 작업은 남아 있습니다.
