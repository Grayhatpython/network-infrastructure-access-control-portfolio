# 04. RADIUS Accounting과 세션 문맥

[README](../README.md) · [Event Workflow](13-event-workflow.md)

## 왜 필요한가

HR의 사용자 ID를 실제로 제어할 스위치 세션과 연결하기 위해 Accounting을 사용했습니다. 사용자 인증 정책만으로는 CoA 대상 NAS·포트·세션을 특정하기 어렵습니다.

```text
Event.username → radacct → Session ID / NAS IP / Port / MAC → CoA 대상
```

## 사용하는 정보

| 정보 | 역할 |
|---|---|
| `username` | HR 계정과 세션 연결 |
| `acctsessionid`, `radacctid` | RADIUS 세션 식별값과 DB 행 식별값 |
| `nasipaddress`, `nasportid` | 인증 스위치와 접속 포트 |
| `callingstationid` | 단말 MAC, 표기 정규화 후 사용 |
| `acctstarttime`, `acctupdatetime`, `acctstoptime` | 세션 시작·갱신·종료 관찰 정보 |

조회 예시는 다음과 같습니다. 계정은 랩 테스트용입니다.

```sql
SELECT radacctid, username, acctsessionid, nasipaddress,
       nasportid, callingstationid, acctstarttime, acctstoptime
FROM radacct
WHERE username = 'A10010'
  AND acctstoptime IS NULL
ORDER BY acctstarttime DESC;
```

## 최신 랩에서 확인한 처리

`DETECTED` Event의 사용자에 대해 활성 세션 후보가 정확히 하나인지 확인했습니다. MAC을 정규화하고 Session/NAS/Port/MAC을 Event에 저장한 뒤 `CONTEXT_RESOLVED`로 전이했습니다. 같은 함수의 재실행에서 중복 변경이 없는 것도 확인했습니다.

`acctstoptime IS NULL`은 활성 **후보** 조건입니다. 종료 로그 유실이나 장비 재시작이 있으면 실제 세션과 다를 수 있습니다. 세션 후보가 없거나 여러 개인 경우의 자동 정책, 최신성 판단과 재시도는 후속 Offline / 다중 세션 처리 과제로 구분합니다.

## 공개 파일 범위

이 문서는 최신 랩의 동작을 설명합니다. Event 기반 문맥 추출 함수와 Event DDL은 현재 공개 Python/SQL 스냅샷에 포함되지 않았습니다. [범위 비교](15-code-coverage.md)
