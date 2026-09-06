# 08. 검증 시나리오와 결과

[README](../README.md) · [현재 상태](../PROJECT_STATUS.md)

## 증거의 범위

아래 검증표는 테스트 사용자 A10010의 부서 이동 시나리오를 단계별로 실행하면서 확인한 결과를 정리한 것입니다. 현재 저장소에는 각 단계의 최신 터미널 출력 전체를 증거 파일로 포함하지 않았으며, 향후 실행 버전과 함께 검증 자료를 추가할 예정입니다.

## 대표 시나리오

테스트 사용자 `A10010`, OLD VLAN21 / `172.16.21.11`, NEW VLAN20 / `172.16.20.11`을 기준으로 합니다. 동일 사용자·단말의 단계별 함수 호출 정상 경로입니다.

| 구간 | 성공 기준 | 개발 기록상 결과 |
|---|---|---|
| 변경 감지 | OLD 21 / NEW 20 감지, 기존 RADIUS·스위치·DHCP·Applied 미변경 | 확인 |
| 문맥 추출 | 활성 세션 후보 1개, MAC 정규화, NAS/Port/Session 저장 | 확인 |
| 정책 적용 | Event NEW와 매핑·Scope·VLAN Attribute 검증, RADIUS 그룹 변경 | 확인 |
| 재인증 | CoA 응답 후 스위치 NEW VLAN 인증, Windows 새 IP | 확인 |
| 새 네트워크 | 새 로그 후보, NEW 예약 `APPLIED`, NEW Pool `RESERVED` | 확인 |
| 이전 자원 정리 | OLD 예약만 삭제·Pool 복귀, NEW 예약 유지 | 확인 |
| 설정 적용 | 문법 검사, DHCP 서비스 active, OLD host 제거·NEW host 유지 | 확인 |
| 최종 완료 | Applied 갱신·Event `DONE` 동시 커밋, 중복 처리 없음 | 확인 |

## DHCP 정리 단계: 19개 완료 조건

1. Event 시작 상태가 `NETWORK_VERIFIED`.
2. NEW VLAN20 Reservation / Pool을 `APPLIED` / `RESERVED`로 재검증.
3. OLD VLAN21 Reservation / Pool을 `APPLIED` / `RESERVED`로 검증.
4. OLD/NEW Scope가 서로 다름을 검증.
5. 정리 대상 Scope / Reservation / IP를 Event Snapshot에 저장.
6. OLD Reservation과 OLD Pool 행을 `FOR UPDATE`로 잠금.
7. NEW Reservation도 잠가 정리 중 보호.
8. OLD Reservation 정확히 1건 삭제.
9. Trigger가 OLD `172.16.21.11`을 `DYNAMIC`으로 변경.
10. NEW `172.16.20.11`은 `APPLIED` / `RESERVED` 유지.
11. Event를 `DHCP_DB_CLEANED`로 변경.
12. DB 트랜잭션 커밋.
13. `sync-dhcp-from-db.py` 성공.
14. `dhcpd -t` 성공.
15. `isc-dhcp-server` active 확인.
16. OLD static host block 제거 확인.
17. NEW static host block 유지 확인.
18. Event를 `DHCP_CLEANED`로 변경.
19. 이 시점의 `hr_managed_user`는 OLD VLAN21 유지.

**결과:** 위 19개 완료 조건을 단계별 실습에서 해당 완료 조건을 확인했습니다.

## 최종 확정 단계: 19개 완료 조건

1. Event 시작 상태가 `DHCP_CLEANED`.
2. `hr_managed_user`는 OLD VLAN21.
3. RADIUS Credential 정상.
4. RADIUS Group은 NEW VLAN20.
5. OLD Reservation 없음.
6. OLD IP는 `DYNAMIC`.
7. NEW Reservation은 `APPLIED`.
8. NEW IP는 `RESERVED`.
9. `hr_managed_user` 행을 `FOR UPDATE`로 잠금.
10. Applied 상태가 Event OLD와 일치.
11. `hr_managed_user`를 Event NEW로 갱신.
12. `last_applied_at` 기록.
13. Event를 `DONE`으로 변경.
14. `completed_at` 기록.
15. Applied 갱신과 Event 완료가 같은 트랜잭션에 포함.
16. 커밋 후 Desired와 Applied 일치.
17. `open_username = NULL`.
18. 같은 완료 함수 재실행 시 `ALREADY_DONE`.
19. 동일 Desired/Applied에 새로운 `DEPT_MOVE`가 생성되지 않음.

**결과:** 위 19개 완료 조건을 단계별 실습에서 해당 완료 조건을 확인했습니다. 두 체크리스트는 기능 조건이며 ‘38개 자동화 테스트가 통과했다’는 의미가 아닙니다.

## 재현 시 남길 증거

| 영역 | 기록할 것 |
|---|---|
| Event | event_id, event_type, state, OLD/NEW 정책, 단계별 시각 |
| RADIUS | 사용자의 그룹, 응답 VLAN Attribute, 새 인증 결과 |
| 스위치 | 대상 포트의 Authorized 상태와 VLAN |
| 단말 | 변경 전후 `ipconfig /all` |
| DHCP | 새 DHCPACK, OLD/NEW Reservation·Pool, 설정 host block |
| 완료·재실행 | Applied 값, `DONE`, `ALREADY_DONE`, 열린 Event 해제 |

증거를 추가할 때는 수집 시각·실행한 코드 버전·실제 결과를 함께 남깁니다. 현재 저장소의 구버전 HR 스냅샷으로 위 전체 검증이 실행되는 것으로 해석하지 않습니다.

## 아직 검증하지 않은 범위

- 자동 Worker에 의한 전체 실행과 HR timer 운영.
- 중복 Worker·여러 사용자·여러 스위치·다중 세션 동시 처리.
- CoA 전송 직후 프로세스 종료, ACK 유실 등 불확실한 외부 요청 처리.
- 지연·중복 DHCP 로그, 기존 임대와 동적 Pool 재사용의 정합성.
- ERROR / Retry / TIMEOUT / SUPERSEDED / Offline 전체 경로.
- 퇴사자 전체 차단·회수, MAB 정책, ACL·방화벽·HA 전환 후 회귀.
- 처리 시간, 가용성, 부하 한계, 성공률의 정량 측정.
