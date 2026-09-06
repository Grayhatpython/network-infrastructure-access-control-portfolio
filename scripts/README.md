# 공개 스크립트 안내

[README](../README.md) · [공개 코드 범위](../docs/15-code-coverage.md)

현재 Repository의 두 Python 스크립트는 아래 실행 범위를 구현하고 있습니다. 최신 Event Workflow 전체는 아직 해당 실행 경로에 통합되지 않았습니다.

| 스크립트 | 현재 공개 실행 경로 |
|---|---|
| [sync-dhcp-from-db.py](sync-dhcp-from-db.py) | DB 정책 조회 → 설정 생성 → 문법 검사 → 비교·백업·교체 → 재시작·상태 반영 |
| [sync-hr-to-radius.py](sync-hr-to-radius.py) | HR 조회·검증 → Desired/Applied 비교 → 변경 로그 → Stage 갱신 |

HR 파일의 일부 함수 정의가 전체 워크플로의 자동 호출을 뜻하지 않습니다. 최신 Event 생성·문맥 추출·CoA·검증·정리·완료 함수와 Dispatcher는 현재 배포 파일에 포함되지 않았습니다.

## 실행 전 확인할 범위

환경 설정 예시는 `config/examples`에 있습니다. 실제 비밀번호, 인증서, 계정 권한, FreeRADIUS 기본 스키마, 최신 랩의 추가 DDL·Trigger는 따로 준비해야 합니다. `systemd/hr-radius-sync.*.example`을 설치하는 것만으로 최신 Event 자동화가 활성화되지는 않습니다.

공개 DHCP 파일의 후속 점검 사항은 [코드 범위 문서](../docs/15-code-coverage.md)에 정리했습니다. DHCP 스크립트의 추가 검증 항목은 코드 범위 문서에 정리했습니다.
