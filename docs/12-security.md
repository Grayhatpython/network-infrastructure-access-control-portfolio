# 12. 공개 저장소 자료 관리

## 공개 금지 항목

다음 값은 GitHub Public Repository에 올리지 않습니다.

```text
RADIUS Shared Secret
Oracle Password
MySQL Password
802.1X Test Password
NT Password Hash
Private Key
실제 개인 계정명/개인정보
```

## Config 관리

실제 파일:

```text
/etc/hr-radius-sync.ini
/etc/dhcp-db-sync.cnf
```

Repository:

```text
config/examples/hr-radius-sync.ini.example
config/examples/dhcp-db-sync.cnf.example
```

## Screenshot

원본 VMware Screenshot에는 로컬 Host의 파일 경로가 표시될 수 있으므로 공개본은 필요한 영역만 남겼습니다.

## Secret이 이미 Git에 들어갔다면

단순히 다음 commit에서 삭제하는 것으로 끝나지 않습니다.

1. Secret 자체 교체
2. 필요하면 Git history 정리
3. 새 Secret은 외부 config / environment / secret store로 관리
