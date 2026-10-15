# Security Assessment - LDAP Authentication API

- **Target:** `http://ldap-api:8000`
- **Tool:** ProjectDiscovery Nuclei v3.11.1, templates v10.5.0
- **Scan date:** 2026-10-15
- **Scope:** 11,102 templates loaded; 13,253 HTTP connections

## Current Scan Summary

| Severity | Findings |
|:---|---:|
| Critical | 0 |
| High | 0 |
| Medium | 0 |
| Low / Info | 2 |

Both remaining matches are informational: missing HSTS on the HTTP endpoint and Uvicorn technology identification.

## Remaining Matches

- **`http-missing-security-headers:strict-transport-security`**
  - The API currently serves plain HTTP. HSTS is meaningful only after a trusted HTTPS endpoint is configured; setting it on HTTP responses would not secure the transport.
- **`tech-detect:uvicorn`**
  - Informational identification of the ASGI server, not an exploitable vulnerability by itself. The server identity is retained rather than obscured and reported as a code fix.

Nuclei also probed ports `4040`, `5814`, and `9780`; all refused connections. These are closed ports, not findings on the LDAP API's configured port `8000`.

## Code Changes Verified

- Kept Swagger UI, ReDoc, and OpenAPI available and protected `/docs`, `/redoc`, `/openapi.json`, and `/docs/oauth2-redirect` with HTTP Basic authentication. The username is `apikey`; the password is the current hot-rotated API key. Unauthenticated requests receive `401`; authenticated requests receive `200`.
- Added CSP, `X-Frame-Options`, `X-Content-Type-Options`, `Referrer-Policy`, `Permissions-Policy`, CORP, COEP, COOP, and `X-Permitted-Cross-Domain-Policies`.
- Restricted CORS to `http://localhost:8080`; the previous arbitrary-origin finding did not recur.
- The latest Nuclei scan no longer reports public API documentation or missing headers other than HSTS.

## Remaining Work

Configure HTTPS with a trusted certificate before enabling HSTS. Uvicorn identification remains an informational technology result.
