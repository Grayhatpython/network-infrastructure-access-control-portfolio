# FreeRADIUS Config Notes

Public repository에는 실제 `clients.conf`의 Shared Secret이나 인증서 Private Key를 포함하지 않습니다.

핵심 설정 포인트:

```text
sites-enabled/default
  authorize { sql }
  accounting { sql }

sites-enabled/inner-tunnel
  authorize { sql }

mods-enabled/sql
  -> mods-available/sql
```

Cisco Authenticator 설정에서는 RADIUS server IP, auth/acct port와 shared secret을 사용하지만 secret은 `<RADIUS_SHARED_SECRET>` 형태로만 문서화합니다.
