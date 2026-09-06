# 프로젝트 구현 상태

[README](README.md) · [검증 상세](docs/08-validation.md) · [공개 코드 범위](docs/15-code-coverage.md)

**문서 기준: 2026-09-06.** 현재 상태는 단계별 실습에서 직접 확인한 정상 경로를 기준으로 정리했습니다. 저장소의 공개 스크립트와 최신 랩의 단계별 구현 범위에는 일부 차이가 있으며, 아래 표에서 이를 구분합니다.

## 상태 표기

| 표기 | 뜻 |
|---|---|
| 랩 검증 완료 | 해당 기능·조건을 랩 환경에서 실행하여 결과를 확인함 |
| 공개 코드 포함 | 저장소 파일에서 구현을 확인할 수 있음. 실행 환경 전체가 포함됐다는 뜻은 아님 |
| 설계 / 예정 | 방향을 정했거나 구현을 계획 중. 완료 성과에 포함하지 않음 |

## 기능별 현황

| 영역 | 최신 랩의 위치 | 공개 저장소와의 차이 |
|---|---|---|
| 802.1X / Dynamic VLAN | 인증 및 VLAN 할당 검증 완료 | 구성 설명과 예시 포함, 전체 장비 설정 미포함 |
| RADIUS Accounting | 사용자·세션·NAS·포트·MAC 연결 검증 | 조회 방법 포함 |
| DHCP / IPAM | 이력 구조화, 최초 예약, Pool 상태·설정 반영 검증 | 생성 스크립트·기본 스키마 포함, 전체 수집 Trigger 미포함 |
| DHCP timer | 서비스·주기 실행 구성 확인 | `.service`, `.timer` 포함 |
| Oracle HR → RADIUS | 별도 HR 서버 조회와 정책 동기화 검증 | 공개 HR `main()`은 변경 감지와 Stage 갱신까지 활성 |
| Desired / Applied | 분리 및 변경 감지 검증 | 관련 테이블과 비교 함수 포함 |
| Event Journal / 세션 문맥 | Event 생성과 `CONTEXT_RESOLVED` 검증 | 최신 Event DDL·함수 미포함 |
| RADIUS 정책·CoA | `RADIUS_APPLIED → COA_SENT` 단계별 호출 검증 | 최신 Event 기반 실행 함수 미포함 |
| 네트워크 검증 | 새 DHCP 증거와 신규 예약 확인, `NETWORK_VERIFIED` | 조건·설계 문서 제공 |
| 이전 DHCP 자원 정리 | DB 정리·설정 반영 후 `DHCP_CLEANED` | 삭제 Trigger 포함, 최신 이벤트 통합 함수 미포함 |
| 최종 완료 | Applied 갱신과 `DONE` 커밋, 재실행 확인 | 완료 조건 문서 제공 |
| Worker / Dispatcher | 다음 자동화 구현 단계 | 미구현 |
| Retry / TIMEOUT / SUPERSEDED / Offline | 후속 설계·구현 예정 | 미구현 |
| 퇴사자 전체 처리 / MAB | 확장 예정 | 부서 이동 완료와 구분 |
| VLAN ACL / 방화벽 / DMZ / HA | 네트워크 확장 설계 단계 | 목표 구조 문서 제공, 적용·장애 전환 검증 전 |

## 최근 정상 경로 체크포인트

- [x] `DEPT_MOVE`: OLD VLAN21 / NEW VLAN20 감지
- [x] `DETECTED`: 작업을 Event로 기록하고 중복 생성 방지 확인
- [x] `CONTEXT_RESOLVED`: 활성 세션 후보 1개 및 NAS/Port/MAC 저장 확인
- [x] `RADIUS_APPLIED`: `VLAN_21 → VLAN_20` 변경, 재실행 중복 변경 없음
- [x] `COA_SENT`: Python을 통한 CoA 단계 실행 및 ACK 확인
- [x] `NETWORK_VERIFIED`: 새 VLAN DHCP 증거와 신규 Reservation/Pool 검증
- [x] `DHCP_DB_CLEANED`: 이전 예약 삭제, 이전 Pool `DYNAMIC`, 신규 예약 보호
- [x] `DHCP_CLEANED`: 설정 동기화, 문법 검사, 서비스 및 OLD/NEW host 확인
- [x] `DONE`: Applied 갱신과 Event 완료를 같은 트랜잭션으로 커밋
- [x] 재실행 `ALREADY_DONE`, `open_username = NULL`, Desired/Applied 일치 시 새 부서 이동 없음
- [ ] 한 번 실행할 때 현재 State에 따라 다음 단계 하나를 고르는 Worker
- [ ] 다중 사용자·다중 스위치·중복 작업자·장애 주입 검증
- [ ] HR Workflow timer로 전체 흐름 자동 실행

## 지금 이어갈 순서

현재 `DONE` 기준선을 보존하고 네트워크 역할·통신 정책을 정리합니다. 필요한 네트워크 변경을 적용한 뒤 동일 부서 이동 시나리오를 회귀 검증하고, Worker / Dispatcher 구현으로 복귀합니다. [단계와 종료 조건](docs/11-roadmap.md)
