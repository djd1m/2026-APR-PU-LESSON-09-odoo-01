# Completion: Auth & Security (auth-security)

## Integration Checklist
- [ ] remont_auth module installs without errors
- [ ] Register endpoint rejects role field
- [ ] Login sets httpOnly cookie
- [ ] /me returns user data from cookie
- [ ] Logout clears cookie
- [ ] Startup validation crashes on missing JWT_SECRET
- [ ] All 7 tests pass

## Deployment Notes
- JWT_SECRET must be set in .env (min 32 chars, random)
- YUKASSA_SECRET_KEY must be set (even if empty for MVP)
- MINIO_ACCESS_KEY, MINIO_SECRET_KEY must be set
- PyJWT must be in odoo/requirements.txt

## Monitoring
- Failed login attempts (rate limiting at 5/min/IP recommended)
- JWT creation rate (anomaly detection)
- Startup validation failures in container logs
