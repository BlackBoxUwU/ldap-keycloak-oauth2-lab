# Security Vulnerability Assessment Report - LDAP Authentication API

- **Target Component:** FastAPI LDAP Authentication & Directory Service (`http://ldap-api:8000`)
- **Scan Tool:** ProjectDiscovery Nuclei v3.11.1 (Templates v10.5.0)
- **Scan Date:** 2026-10-14
- **Assessment Scope:** Dynamic Application Security Testing (DAST) across 11,102 signed templates.

---

## 📊 Summary of Identified Findings

| Severity | Count | Status |
|:---|:---:|:---|
| **Critical** | 0 | None |
| **High** | 0 | None |
| **Medium** | 0 | None |
| **Low / Info** | 15 | Identified (CORS wildcard, API schema exposure, headers) |

---

## 🔍 Detailed List of Identified Vulnerabilities and Security Gaps

### 1. CORS Misconfiguration: Overly Permissive Arbitrary Origin
- **`cors-misconfig:arbitrary-origin`**
  - *Severity:* **Info / Low**
  - *Affected URL:* `http://ldap-api:8000`
  - *Triggered Origin:* `cors_origin="http://localhost.bjttr.com"`
  - *Finding:* The CORS middleware is configured with `allow_origins=["*"]` along with `allow_credentials=True`.
  - *Risk:* Arbitrary external domains can initiate cross-origin requests. An attacker hosting a malicious site could make authorized requests to internal API endpoints on behalf of authenticated users if credentials/tokens are transmitted.
  - *Remediation:* Restrict `allow_origins` strictly to trusted frontend origins (e.g., `http://localhost:8080` and the internal container hostname) instead of the wildcard `*`.

---

### 2. Public Interactive API Documentation Exposure
- **`swagger-api`** (`http://ldap-api:8000/docs`)
- **`openapi`** (`http://ldap-api:8000/openapi.json`)
- **`redoc-api-docs`** (`http://ldap-api:8000/redoc`)
  - *Finding:* FastAPI automatically exposes Swagger UI, ReDoc, and the OpenAPI schema publicly without requiring authentication.
  - *Risk:* Attackers obtain a complete map of all internal endpoints, request bodies, models, parameter schemas, and authentication schemes, making targeted exploitation significantly easier.
  - *Remediation:* Disable interactive docs in production (`FastAPI(docs_url=None, redoc_url=None, openapi_url=None)`) or restrict access behind authentication.

---

### 3. Missing HTTP Security Headers
The FastAPI response does not set security-hardening headers:

- **`http-missing-security-headers:content-security-policy`**
- **`http-missing-security-headers:strict-transport-security` (HSTS)**
- **`http-missing-security-headers:x-frame-options`**
- **`http-missing-security-headers:x-content-type-options`**
- **`http-missing-security-headers:referrer-policy`**
- **`http-missing-security-headers:permissions-policy`**
- **`http-missing-security-headers:cross-origin-resource-policy`**
- **`http-missing-security-headers:cross-origin-embedder-policy`**
- **`http-missing-security-headers:cross-origin-opener-policy`**
- **`http-missing-security-headers:x-permitted-cross-domain-policies`**

---

### 4. Technology Fingerprinting
- **`tech-detect:uvicorn`**
  - *Finding:* Server responds with `server: uvicorn` header, disclosing the exact ASGI server implementation.
  - *Remediation:* Strip the `Server` header in response middleware.

---

## 🛠️ Next Steps: Granular Remediation Plan (Phase 2)
1. **Commit 1:** Fix CORS policy in `app/main.py`: Replace wildcard `*` with explicit trusted frontend origins.
2. **Commit 2:** Disable or restrict public Swagger / OpenAPI / ReDoc documentation in production mode.
3. **Commit 3:** Implement custom middleware or security headers middleware to inject `X-Frame-Options`, `X-Content-Type-Options`, and strip the `Server` header.
