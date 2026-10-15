# Security Vulnerability Assessment Report - LDAP Authentication API

- **Target Component:** FastAPI LDAP Authentication & Directory Service (`http://ldap-api:8000`)
- **Scan Tool:** ProjectDiscovery Nuclei v3.11.1 (Templates v10.5.0)
- **Scan Date:** 2026-10-15
- **Assessment Scope:** Dynamic Application Security Testing (DAST); 11,102 templates loaded.

---

## Summary of Identified Findings

Nuclei reported 14 findings, all with **Info** severity. These are informational detections and hardening gaps, not evidence of 14 exploitable vulnerabilities.

| Severity | Count | Status |
|:---|:---:|:---|
| **Critical** | 0 | None detected |
| **High** | 0 | None detected |
| **Medium** | 0 | None detected |
| **Low / Info** | 14 | 10 missing-header findings, 3 public documentation endpoints, and 1 technology fingerprint |

---

## Detailed Findings

### 1. Public API Documentation

- **`swagger-api`** — `http://ldap-api:8000/docs`
- **`openapi`** — `http://ldap-api:8000/openapi.json`
- **`redoc-api-docs`** — `http://ldap-api:8000/redoc`

The interactive Swagger UI, ReDoc, and OpenAPI schema are publicly accessible. They disclose the API structure and request schemas, which may make targeted probing easier.

**Remediation:** Disable these endpoints in production or restrict them to authorized users/networks.

### 2. Missing HTTP Security Headers

Nuclei reported these ten missing headers:

- **`http-missing-security-headers:content-security-policy`**
- **`http-missing-security-headers:strict-transport-security` (HSTS)**
- **`http-missing-security-headers:x-frame-options`**
- **`http-missing-security-headers:x-content-type-options`**
- **`http-missing-security-headers:referrer-policy`**
- **`http-missing-security-headers:permissions-policy`**
- **`http-missing-security-headers:cross-origin-resource-policy` (CORP)**
- **`http-missing-security-headers:cross-origin-embedder-policy` (COEP)**
- **`http-missing-security-headers:cross-origin-opener-policy` (COOP)**
- **`http-missing-security-headers:x-permitted-cross-domain-policies`**

HSTS requires HTTPS to be useful; the API is currently served over HTTP.

### 3. Technology Fingerprinting

- **`tech-detect:uvicorn`**
  - **Finding:** The ASGI server implementation is identifiable.
  - **Remediation:** Review response headers and deployment configuration to reduce unnecessary server fingerprinting.

### 4. CORS Finding from the Earlier Scan

- **`cors-misconfig:arbitrary-origin`**
  - **Status:** Not reported by the 2026-10-15 scan. The wildcard origin was replaced with `http://localhost:8080`.
  - **Note:** The current scan did not reproduce the earlier CORS finding; retain the explicit-origin configuration.

---

## Scan Notes

Nuclei also probed ports `4040` and `5814`, which refused connections. These are closed ports, not findings against the LDAP API's configured HTTP port `8000`.

## Remediation Plan

1. **Block 1:** Restricted CORS to the dashboard origin. The earlier arbitrary-origin finding did not recur in this scan.
2. **Next:** Disable or restrict public Swagger, OpenAPI, and ReDoc endpoints.
3. **Later:** Add appropriate HTTP security headers and reduce unnecessary server fingerprinting; configure HTTPS before enabling HSTS.
