# Auth Testing Playbook

Save this playbook and refer during testing.

## Verify admin seeding & MongoDB
```
mongosh
use venture_crm
db.users.find({role: "admin"}).pretty()
db.funds.find().pretty()
```
- Admin bcrypt hash starts with `$2b$`.
- Two funds seeded: `Beta Fund` (slug: beta) and `Fund I` (slug: fund-i).

## API smoke test
```
BASE=$(grep REACT_APP_BACKEND_URL /app/frontend/.env | cut -d'=' -f2)
curl -c /tmp/c.txt -X POST "$BASE/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@fund.com","password":"admin123"}'
curl -b /tmp/c.txt "$BASE/api/auth/me"
curl -b /tmp/c.txt "$BASE/api/funds"
```
