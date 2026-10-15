# Security Vulnerability Assessment Report - LDAP Authentication API

- **Target Component:** FastAPI LDAP Authentication & Directory Service (`http://ldap-api:8000`)
- **Scan Tool:** ProjectDiscovery Nuclei v3.11.1 (Templates v10.5.0)
- **Baseline Scan Date:** 2026-10-15
- **Post-Block-1 Scan Date:** 2026-10-15
- **Assessment Scope:** Dynamic Application Security Testing (DAST); 11,102 templates loaded.

---

## Summary

The baseline scan found 14 informational findings on LDAP. After Block 1, the full Nuclei scan reports only the missing HSTS header. The 13 other baseline findings are no longer detected.

| Scan | Critical | High | Medium | Low / Info |
|:---|---:|---:|---:|---:|
| Baseline (before Block 1) | 0 | 0 | 0 | 14 |
| Post-Block-1 validation | 0 | 0 | 0 | 1 |

These Nuclei results are informational detections and hardening gaps, not evidence of exploitable vulnerabilities.

---

## Current Finding

### Missing HTTP Strict Transport Security

- **`http-missing-security-headers:strict-transport-security`**
  - **Status:** Pending HTTPS deployment. The LDAP API is served over HTTP; sending HSTS over plain HTTP would not provide transport security.
  - **Next step:** Configure TLS at the service or trusted reverse-proxy boundary, then enable HSTS there.

---

## Block 1 Remediation and Validation

The LDAP baseline contributed 14 findings to the combined baseline of 35 findings across the frontend, backend, and LDAP services. Block 1 addressed 13 of those 14 findings:

- Disabled public Swagger UI, ReDoc, and OpenAPI endpoints (`/docs`, `/redoc`, and `/openapi.json`). Each now returns `404`.
- Added Content-Security-Policy, X-Frame-Options, X-Content-Type-Options, Referrer-Policy, Permissions-Policy, Cross-Origin-Resource-Policy, Cross-Origin-Embedder-Policy, Cross-Origin-Opener-Policy, and X-Permitted-Cross-Domain-Policies.
- Disabled the Uvicorn `Server` response header.
- Replaced the wildcard CORS origin with the dashboard origin `http://localhost:8080` in the earlier block.

The post-remediation full scan confirmed that the documentation exposure, missing headers other than HSTS, and Uvicorn fingerprint are no longer detected. Nuclei also probed ports `4040`, `5814`, and `9780`; their connection refusals are closed ports, not findings against the LDAP API on port `8000`.

---

## Three-Block Remediation Plan

The 2026-10-15 baseline contained 35 findings: 12 frontend, 9 backend, and 14 LDAP.

1. **Block 1 — LDAP API (13 of 35 baseline findings):** Completed and re-scanned. Only HSTS remains, pending HTTPS.
2. **Block 2 — Backend API (9 baseline findings):** Add the missing API security headers and reduce Express fingerprinting. The older development-environment finding is already mitigated by `NODE_ENV=production`.
3. **Block 3 — Frontend and transport (12 frontend findings plus LDAP HSTS):** Review remaining frontend headers, update the NGINX image, remove the external font/SRI finding, and configure HTTPS before enabling HSTS.
