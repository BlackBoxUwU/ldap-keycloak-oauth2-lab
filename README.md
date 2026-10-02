# LDAP Authentication Service (FastAPI + OpenLDAP)

This microservice provides LDAP-backed user authentication with integrated **dynamic API Key (`x-api-key`) validation** and **zero-downtime hot secret rotation**.

## Architecture & Security
- **Port**: `8000` (FastAPI) / `389` (OpenLDAP directory)
- **Security Validation**: Every authentication request to `/login` requires a valid `x-api-key` header matching the active shared secret.
- **Hot Secret Reload**: Dynamically reads `/shared-secrets/api_secret.txt` on every request. When the rotator updates the secret, LDAP validation switches seamlessly without restarting the container.

## Endpoints
- `GET /health` (Public): Health status of API and configured LDAP server.
- `GET /status` (Protected): Diagnostics showing preview of the current active secret.
- `POST /login` (Protected): Authenticates username and password against OpenLDAP directory.

### Sample LDAP Seed Credentials:
- `alice` / `alice123`
- `bob` / `bob123`

## Running Locally with Docker
```bash
docker build -t ldap-api .
docker run -p 8000:8000 -v shared_secrets:/shared-secrets ldap-api
```
