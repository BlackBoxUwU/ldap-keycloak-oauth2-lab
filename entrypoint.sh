#!/bin/bash
set -e
mkdir -p /var/log/ldap-api /var/run/fail2ban
touch /var/log/ldap-api/access.log /var/log/fail2ban.log
rm -f /var/run/fail2ban/fail2ban.sock /var/run/fail2ban/fail2ban.pid

uvicorn app.main:app --host 0.0.0.0 --port 8000 --no-server-header &
sleep 1
fail2ban-client -x start

echo "[ldap-api-protected] FastAPI LDAP Auth Service + Fail2Ban running."
exec tail -F /var/log/fail2ban.log
