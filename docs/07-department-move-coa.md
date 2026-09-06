# 07. 부서 이동과 CoA: 정책 변경을 실제 접속에 반영하기

[README](../README.md) · [검증 결과](08-validation.md) · [상태 정의](13-event-workflow.md)

## 처음 발견한 문제

Oracle의 부서를 변경하고 Python을 실행하면 `radusergroup`은 바뀌었지만, 이미 인증된 스위치 포트와 클라이언트의 IP는 이전 상태로 남았습니다. 정책 DB 수정과 현재 세션의 재인증이 별도 작업이라는 점을 확인했습니다.

## 두 번의 검증 흐름

| 시점 | 방향 | 확인한 범위 |
|---|---|---|
| 초기 수동 검증 | VLAN20 → VLAN21 | RADIUS 정책, CoA 재인증, 신규 IP, 이전 예약 정리 |
| 최신 Event 검증 | VLAN21 → VLAN20 | 단계별 Event 처리, 신규 증거 검증, 이전 예약 정리, Applied와 `DONE` 확정 |

방향이 바뀐 것은 문서 오류가 아니라 서로 다른 검증 시나리오입니다. 이 포트폴리오의 대표 결과는 최신 VLAN21 → VLAN20입니다.

## 최신 정상 경로

```text
Oracle Desired = VLAN20 / Applied = VLAN21
    ↓
DETECTED → CONTEXT_RESOLVED
    ↓ 현재 세션의 NAS / Port / Session / MAC 확보
RADIUS_APPLIED
    ↓ VLAN_21 → VLAN_20 정책 변경
COA_SENT
    ↓ 재인증 요청 결과 기록
NETWORK_VERIFIED
    ↓ 새 DHCP 증거 + NEW APPLIED / RESERVED 확인
DHCP_DB_CLEANED
    ↓ OLD 예약 삭제 / OLD Pool DYNAMIC / DB 커밋
DHCP_CLEANED
    ↓ DHCP 설정 동기화·문법·서비스·host block 확인
DONE
    ↓ Applied VLAN20 갱신과 Event 완료를 함께 커밋
Desired == Applied
```

## CoA에서 확인한 문제

Port Bounce와 `reauthenticate-type=rerun`을 시험할 때, 스위치 세션이 사라지고 Windows의 이전 IP만 남는 현상을 겪었습니다. 이후 랩에서 기본 `subscriber:command=reauthenticate` 방식으로 새 VLAN 인증과 DHCP 할당을 확인했습니다. 특정 가상 장비에서의 관찰 결과이며 모든 Cisco 환경의 동작을 일반화하지 않습니다.

CoA/Disconnect는 현재 세션에 변경을 요청하는 절차입니다. 응답 이후 실제 재인증·주소 획득은 별도로 확인했습니다. [RFC 5176](https://www.rfc-editor.org/rfc/rfc5176)

## 완료를 판단하는 증거

스위치 Authorized/VLAN과 Windows IP를 수동으로 교차 확인했습니다. Event의 자동 검증은 기록된 MAC·목표 VLAN·새 DHCP 로그·Reservation·Pool을 대조하는 범위입니다. 스위치 CLI를 자동 조회하는 기능을 구현했다고 주장하지 않습니다.

`lease_log_watermark`는 CoA 준비 시점의 로그 기준값입니다. 그보다 큰 `log_id`를 대상으로 조회해 이미 수집된 과거 이력을 재사용할 가능성을 줄입니다. 지연 도착 로그, 동시 INSERT·커밋 순서, 다른 원인의 DHCP 갱신을 완전히 배제하지는 못하므로 시각·세션·장비 상태를 함께 검증하는 개선을 남겼습니다.

## 예약을 정리하는 순서

새 IP가 정상 확인되기 전까지 OLD 예약을 유지합니다. NEW 예약이 `APPLIED`, NEW Pool이 `RESERVED`인지 검증한 뒤 OLD/NEW Scope가 다름을 확인하고, OLD 대상 정보를 Snapshot으로 저장합니다. 관련 행 잠금 후 OLD 예약 1건만 삭제하며 NEW 예약은 보호합니다.

이 순서는 복귀에 필요한 예약 자원을 먼저 없애지 않기 위한 것입니다. 자동 롤백 전체나 통신 무중단을 검증했다는 의미는 아닙니다.
