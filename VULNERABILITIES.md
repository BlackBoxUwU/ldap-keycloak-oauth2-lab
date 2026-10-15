# Security Vulnerability Assessment Report - LDAP Authentication API

- **Target Component:** FastAPI LDAP Authentication & Directory Service (`http://ldap-api:8000`)
- **Scan Tool:** ProjectDiscovery Nuclei v3.11.1 (Templates v10.5.0)
- **Baseline Scan Date:** 2026-10-15
- **Post-Block-1 Scan Date:** 2026-10-15
- **Assessment Scope:** Dynamic Application Security Testing (DAST); 11,102 templates loaded.

---

## Summary

The baseline scan found 14 informational findings on LDAP. The latest full scan reports two informational detections: missing HSTS and the Uvicorn technology fingerprint. The documentation is now access-controlled and the missing security headers other than HSTS are corrected.

| Scan | Critical | High | Medium | Low / Info |
|:---|---:|---:|---:|---:|
| Baseline (before Block 1) | 0 | 0 | 0 | 14 |
| Post-Block-1 validation | 0 | 0 | 0 | 2 |

These Nuclei results are informational detections and hardening gaps, not evidence of exploitable vulnerabilities.

---

## Remaining Informational Findings

### Missing HTTP Strict Transport Security

- **`http-missing-security-headers:strict-transport-security`**
  - **Status:** Pending HTTPS deployment. The LDAP API is served over HTTP; sending HSTS over plain HTTP would not provide transport security.
  - **Next step:** Configure TLS at the service or trusted reverse-proxy boundary, then enable HSTS there.

- **`tech-detect:uvicorn`**
  - **Status:** Informational technology fingerprint. The API runs on Uvicorn; removing its version header alone would only mask the detector, not fix an exploitable weakness. It is retained transparently in the results.

---

## Block 1 Remediation and Validation

The LDAP baseline contributed 14 informational findings to the combined baseline of 35 findings across the frontend, backend, and LDAP services. Block 1 makes these code-level changes:

- Kept Swagger UI, ReDoc, and OpenAPI available, but protected `/docs`, `/redoc`, `/openapi.json`, and `/docs/oauth2-redirect` with HTTP Basic authentication using username `apikey` and the current rotating API key as the password. Unauthenticated requests receive `401`; authorized requests receive `200`. This is access control, not removal of the documentation.
- Added Content-Security-Policy, X-Frame-Options, X-Content-Type-Options, Referrer-Policy, Permissions-Policy, Cross-Origin-Resource-Policy, Cross-Origin-Embedder-Policy, Cross-Origin-Opener-Policy, and X-Permitted-Cross-Domain-Policies.
- Replaced the wildcard CORS origin with the dashboard origin `http://localhost:8080` in the earlier block.

The post-remediation full scan confirmed that public documentation exposure is no longer detected and the missing headers other than HSTS are corrected. Uvicorn remains detectable and is reported as informational rather than being masked as a vulnerability fix. Nuclei also probed ports `4040` and `5814`; their connection refusals are closed ports, not findings against the LDAP API on port `8000`.

---

## Three-Block Remediation Plan

The 2026-10-15 baseline contained 35 findings: 12 frontend, 9 backend, and 14 LDAP.

1. **Block 1 — LDAP API:** Completed and re-scanned. Public documentation now requires authentication, missing headers are corrected, and prior CORS is restricted. Remaining LDAP reports are HSTS pending HTTPS and an informational Uvicorn fingerprint.
2. **Block 2 — Backend API (9 baseline findings):** Add the missing API security headers and reduce Express fingerprinting. The older development-environment finding is already mitigated by `NODE_ENV=production`.
3. **Block 3 — Frontend and transport (12 frontend findings plus LDAP HSTS):** Review remaining frontend headers, update the NGINX image, remove the external font/SRI finding, and configure HTTPS before enabling HSTS.
