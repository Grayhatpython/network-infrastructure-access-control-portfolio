# 공개 포트폴리오의 정보 관리 원칙

이 저장소는 Public Portfolio를 전제로 합니다.

## 포함하지 않는 정보

- 실제 RADIUS Shared Secret
- 실제 Oracle/MySQL Password
- 실제 NT Password Hash
- Private Key
- 개인 식별 정보
- 실제 운영 장비 Credential

## Example Config

실제 설정은 `/etc/...`에 두고 Repository에는 `.example`만 유지합니다.

## 이미 유출한 경우

Secret을 Git history에서 지우는 것과 별개로 **Secret 자체를 교체**합니다.
