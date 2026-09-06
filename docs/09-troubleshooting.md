# 09. 트러블슈팅: 증상에서 계층별 원인으로

[README](../README.md)

## 1. Ping은 되지만 EAPOL이 인증 스위치에 도착하지 않음

**증상:** Windows는 802.1X를 시도했지만 스위치에서 인증 교환이 이어지지 않았습니다.

**확인:** Windows VM → VMware VMnet → EVE 외부 NIC → pnet bridge → 가상 스위치 인터페이스를 나누어 EAPOL 프레임을 추적했습니다. EVE 외부 NIC에서는 보이지만 스위치 쪽 인터페이스에서는 보이지 않는 구간을 확인했습니다.

**조치·결과:** 해당 랩 bridge의 link-local 프레임 전달 설정을 조정한 뒤 사용자 인증 창과 ASW까지의 EAPOL 전달을 확인했습니다. bridge 이름과 설정은 해당 환경에 한정됩니다.

**배운 점:** Ping 성공은 EAPOL 전달 성공의 증거가 아닙니다. 인증 프로토콜이 실제로 지나는 계층을 기준으로 점검해야 합니다.

## 2. RADIUS 서버에 인증 로그가 나타나지 않음

**증상:** 단말–ASW 구간의 EAPOL은 보이는데 FreeRADIUS에 요청이 나타나지 않았습니다.

**확인:** ASW 관리 SVI에서 Backbone과 Auth 서버로의 통신, L2/L3 동작 모드, 기본 게이트웨이와 응답 경로를 분리해 확인했습니다.

**정리:** Auth 서버가 다른 VLAN에 있다는 이유만으로 그 VLAN을 ASW trunk에 추가할 필요가 있는 것은 아닙니다. 현재 구조에서는 관리 VLAN 프레임이 Core까지 도달하고 그 뒤 라우팅되는 경로를 먼저 확인했습니다. 이 사례의 단일 최종 원인은 최신 완료 조건만으로 확정하지 않았습니다.

## 3. CoA 성공 응답 뒤 인증 세션이 사라짐

**증상:** Port Bounce 또는 `rerun` 시험 후 스위치는 `No sessions match supplied criteria`를 표시했지만 Windows에는 OLD IP가 남았습니다.

**확인:** CoA 응답, 새 EAPOL 교환, RADIUS Access-Request/Accept, 스위치 세션, DHCP를 순서대로 확인했습니다.

**조치·결과:** 기본 `subscriber:command=reauthenticate` 방식으로 테스트해 새 VLAN 인증과 새 DHCP 주소를 확인했습니다.

**배운 점:** CoA-ACK, 스위치 세션, Windows DHCP 임대는 각각 다른 상태입니다. IP가 화면에 남아 있다는 이유로 네트워크 접근이 계속 허용된다고 판단하지 않았습니다.

## 4. 부서 이동 후 OLD DHCP 예약이 남음

**증상:** NEW VLAN 주소를 받아도 OLD Reservation, OLD Pool의 `RESERVED`, 이전 static host가 유지됐습니다.

**원인·조치:** 예약 생성 흐름에 대응하는 회수 처리가 필요했습니다. NEW 상태를 먼저 확인하고 OLD 예약 1건을 삭제한 뒤 Trigger로 Pool을 복귀시켰습니다. 설정 동기화를 별도 단계로 확인했습니다.

**결과:** 최신 정상 경로에서 OLD host 제거, NEW host 유지와 `DHCP_CLEANED`까지 확인했습니다.

## 5. rsyslog active인데 MySQL 저장 오류

**증상:** `ommysql`에서 로컬 MySQL 소켓 연결 오류가 나지만 rsyslog 서비스는 active였습니다.

**확인·결과:** MySQL과 소켓이 정상인 상태에서 rsyslog를 재시작하자 오류가 사라졌습니다.

**해석:** 초기 서비스 준비 순서에 따른 일시적 접속 실패 가능성이 높았습니다. 시작 순서가 원인이었다고 단정할 전체 타임라인은 확보하지 않았습니다. 재시도·큐 구성은 당시 제안된 개선 사항이며 적용 완료로 기록하지 않습니다.

## 6. SQL Trigger 실행 도구와 문법 혼동

**증상:** DBeaver에서 Trigger를 실행할 때 `DELIMITER` 부근 또는 문장 끝의 구문 오류를 만났습니다.

**확인:** Trigger 본문 문법과 클라이언트의 스크립트 분할·실행 방식을 구분했습니다. 이후 `SHOW TRIGGERS`에서는 Trigger가 확인됐지만 GUI 목록에는 보이지 않는 상황도 있었습니다.

**배운 점:** DB 객체 존재 여부는 실제 DB 조회로 확인하고 GUI 캐시와 구분했습니다. 권한·실행 도구·서버 구문 오류를 같은 문제로 취급하지 않았습니다.

## 7. 생성한 DHCP 후보 설정의 문법 검사 실패

**증상:** Python 서비스 실행 중 `range declaration not allowed here` 오류가 발생했습니다.

**판단:** Python 실행 자체보다 생성된 설정의 블록 구조를 확인해야 하는 문제였습니다.

**설계에 반영:** 후보 설정을 검사한 뒤 교체하는 순서를 사용했습니다. 최신 정리 단계에서는 `dhcpd -t` 성공을 별도의 완료 조건으로 확인했습니다.

## 8. FreeRADIUS SQL 모듈의 인증서 경로 오류

**증상:** SQL 모듈이 참조한 CA 파일이 없어 사전 구성 검사에서 서비스 시작이 실패했습니다.

**판단:** 서비스 설명인 ‘multi-protocol policy server’가 원인이 아니라, 실제 오류의 파일 경로와 모듈 초기화 실패를 확인해야 했습니다.

**정리:** FreeRADIUS→MySQL TLS와 Windows→FreeRADIUS의 EAP 인증서 신뢰는 별도 연결입니다. 당시 제안된 임시 설정을 운영 환경의 보안 완료 상태로 표현하지 않습니다.
