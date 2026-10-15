import base64
import binascii
import os
import secrets
import time
import logging
import threading
from typing import Optional
from fastapi import FastAPI, HTTPException, Header, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from ldap3 import Server, Connection, ALL, SUBTREE

# Logging configuration
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("ldap-auth-service")

app = FastAPI(
    title="LDAP Authentication API with Hot Secret Rotation",
    description="Secured FastAPI service with LDAP backend and dynamic API Key validation",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8080"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from starlette.middleware.base import BaseHTTPMiddleware

class AccessLogMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        client_ip = request.client.host if request.client else "127.0.0.1"
        log_dir = "/var/log/ldap-api"
        try:
            if not os.path.exists(log_dir):
                os.makedirs(log_dir, exist_ok=True)
            log_line = f'{client_ip} - - [{time.strftime("%d/%b/%Y:%H:%M:%S %z")}] "{request.method} {request.url.path} HTTP/1.1" {response.status_code}\n'
            with open(os.path.join(log_dir, "access.log"), "a", encoding="utf-8") as f:
                f.write(log_line)
        except Exception:
            pass
        return response

app.add_middleware(AccessLogMiddleware)


@app.middleware("http")
async def add_security_headers(request, call_next):
    response = None
    if request.url.path in {"/docs", "/redoc", "/openapi.json", "/docs/oauth2-redirect"}:
        credentials = request.headers.get("authorization", "")
        scheme, separator, value = credentials.partition(" ")
        username = password = ""
        try:
            decoded_credentials = base64.b64decode(value, validate=True).decode("utf-8")
            username, separator, password = decoded_credentials.partition(":")
        except (binascii.Error, UnicodeDecodeError):
            separator = ""
        expected_key = get_active_api_secret()

        if (
            scheme.lower() != "basic"
            or not separator
            or username != "apikey"
            or not password
            or not secrets.compare_digest(password, expected_key)
        ):
            from fastapi.responses import JSONResponse

            response = JSONResponse(
                status_code=401,
                content={"detail": "Authentication required to access API documentation."},
                headers={"WWW-Authenticate": 'Basic realm="LDAP API documentation"'},
            )

    if response is None:
        response = await call_next(request)
    if request.url.path in {"/docs", "/redoc", "/openapi.json", "/docs/oauth2-redirect"}:
        response.headers["Content-Security-Policy"] = (
            "default-src 'none'; script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
            "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
            "font-src 'self' data: https://cdn.jsdelivr.net; img-src 'self' data: https://fastapi.tiangolo.com; "
            "connect-src 'self'; frame-ancestors 'none'; base-uri 'none'"
        )
    else:
        response.headers["Content-Security-Policy"] = "default-src 'none'; frame-ancestors 'none'; base-uri 'none'"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    response.headers["Cross-Origin-Resource-Policy"] = "same-origin"
    response.headers["Cross-Origin-Embedder-Policy"] = "require-corp"
    response.headers["Cross-Origin-Opener-Policy"] = "same-origin"
    response.headers["X-Permitted-Cross-Domain-Policies"] = "none"
    return response

# Configuration from Environment
LDAP_HOST = os.getenv("LDAP_HOST", "openldap")
LDAP_PORT = int(os.getenv("LDAP_PORT", "389"))
LDAP_BASE_DN = os.getenv("LDAP_BASE_DN", "dc=example,dc=com")
LDAP_ADMIN_PASSWORD = os.getenv("LDAP_ADMIN_PASSWORD", "adminpassword")
SHARED_SECRET_FILE = "/shared-secrets/api_secret.txt"


def auto_seed_ldap():
    """
    Background worker that connects to OpenLDAP as admin
    and automatically creates OUs and sample users (alice, bob) if not present.
    """
    admin_dn = f"cn=admin,{LDAP_BASE_DN}"
    server = Server(LDAP_HOST, port=LDAP_PORT, get_info=ALL)

    for attempt in range(1, 20):
        try:
            conn = Connection(server, user=admin_dn, password=LDAP_ADMIN_PASSWORD, auto_bind=True)
            logger.info("Connected to OpenLDAP directory server as admin. Checking seed users...")

            users_ou = f"ou=users,{LDAP_BASE_DN}"
            groups_ou = f"ou=groups,{LDAP_BASE_DN}"

            # 1. Create ou=users
            conn.search(LDAP_BASE_DN, f"(ou=users)", search_scope=SUBTREE)
            if not conn.entries:
                conn.add(users_ou, ["organizationalUnit"], {"ou": "users"})
                logger.info("Created LDAP OU: ou=users")

            # 2. Create ou=groups
            conn.search(LDAP_BASE_DN, f"(ou=groups)", search_scope=SUBTREE)
            if not conn.entries:
                conn.add(groups_ou, ["organizationalUnit"], {"ou": "groups"})
                logger.info("Created LDAP OU: ou=groups")

            # 3. Create user alice
            alice_dn = f"uid=alice,{users_ou}"
            conn.search(users_ou, "(uid=alice)", search_scope=SUBTREE)
            if not conn.entries:
                conn.add(
                    alice_dn,
                    ["inetOrgPerson"],
                    {
                        "uid": "alice",
                        "sn": "Smith",
                        "givenName": "Alice",
                        "cn": "Alice Smith",
                        "displayName": "Alice Smith",
                        "mail": "alice@example.com",
                        "userPassword": "alice123",
                    },
                )
                logger.info("Seeded LDAP user: alice (password: alice123)")

            # 4. Create user bob
            bob_dn = f"uid=bob,{users_ou}"
            conn.search(users_ou, "(uid=bob)", search_scope=SUBTREE)
            if not conn.entries:
                conn.add(
                    bob_dn,
                    ["inetOrgPerson"],
                    {
                        "uid": "bob",
                        "sn": "Johnson",
                        "givenName": "Bob",
                        "cn": "Bob Johnson",
                        "displayName": "Bob Johnson",
                        "mail": "bob@example.com",
                        "userPassword": "bob123",
                    },
                )
                logger.info("Seeded LDAP user: bob (password: bob123)")

            # 5. Create group developers
            dev_dn = f"cn=developers,{groups_ou}"
            conn.search(groups_ou, "(cn=developers)", search_scope=SUBTREE)
            if not conn.entries:
                conn.add(dev_dn, ["groupOfNames"], {"cn": "developers", "member": [alice_dn, bob_dn]})
                logger.info("Seeded LDAP group: developers")

            conn.unbind()
            logger.info("✓ OpenLDAP bootstrap & user seeding finished successfully!")
            return
        except Exception as e:
            logger.warning(f"Waiting for OpenLDAP server to be ready (attempt {attempt}/20): {e}")
            time.sleep(2)


@app.on_event("startup")
def on_startup():
    # Run LDAP seeding in a background thread to avoid blocking server start
    t = threading.Thread(target=auto_seed_ldap, daemon=True)
    t.start()


def get_active_api_secret() -> str:
    """
    Dynamically loads the active API secret.
    1. Reads from shared rotated volume (/shared-secrets/api_secret.txt).
    2. Falls back to API_SECRET environment variable.
    3. Falls back to initial default lab key.
    """
    try:
        if os.path.exists(SHARED_SECRET_FILE):
            with open(SHARED_SECRET_FILE, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if content:
                    return content
    except Exception as e:
        logger.warning(f"Could not read shared secret file: {e}")

    return os.getenv("API_SECRET", "initial-lab-secret-key-2026")


def require_api_key(x_api_key: Optional[str] = Header(None, alias="x-api-key")):
    """
    Security dependency: Validates that incoming request possesses the matching x-api-key.
    Supports hot-reloaded secrets without server restart.
    """
    current_key = get_active_api_secret()
    if not x_api_key or x_api_key != current_key:
        masked_received = f"{x_api_key[:4]}***" if x_api_key and len(x_api_key) >= 4 else "None"
        logger.warning(f"Unauthorized access attempt. Received key: {masked_received}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": "Unauthorized",
                "message": "Missing or invalid x-api-key header.",
                "received": masked_received,
            },
        )
    return current_key


class LoginRequest(BaseModel):
    username: str
    password: str


@app.get("/health")
def health():
    """Public health check endpoint (no API Key required)"""
    return {
        "status": "ok",
        "service": "LDAP Authentication API",
        "ldap_host": LDAP_HOST,
        "ldap_port": LDAP_PORT,
    }


@app.get("/status")
def status_endpoint(api_key: str = Depends(require_api_key)):
    """Diagnostic endpoint verifying current rotated API key status"""
    current_key = get_active_api_secret()
    masked = f"{current_key[:4]}...{current_key[-4:]}" if len(current_key) > 8 else "***"
    return {
        "status": "authenticated",
        "service": "LDAP Authentication Service",
        "api_secret_preview": masked,
        "api_secret_length": len(current_key),
    }


@app.post("/login")
def login(request: LoginRequest, api_key: str = Depends(require_api_key)):
    """
    Protected Login Endpoint.
    Requires valid x-api-key header.
    Validates user credentials against OpenLDAP directory.
    """
    logger.info(f"Authenticating LDAP user: {request.username}")

    server = Server(
        LDAP_HOST,
        port=LDAP_PORT,
        get_info=ALL,
    )

    user_dn = f"uid={request.username},ou=users,{LDAP_BASE_DN}"

    connection = Connection(
        server,
        user=user_dn,
        password=request.password,
        auto_bind=False,
    )

    try:
        if connection.bind():
            # Retrieve user display attributes if available
            connection.search(
                search_base=user_dn,
                search_filter="(objectClass=*)",
                search_scope=SUBTREE,
                attributes=["cn", "mail", "displayName", "givenName", "sn"],
            )

            display_name = request.username
            email = f"{request.username}@example.com"

            if connection.entries:
                entry = connection.entries[0]
                if hasattr(entry, "displayName") and entry.displayName.value:
                    display_name = str(entry.displayName.value)
                elif hasattr(entry, "cn") and entry.cn.value:
                    display_name = str(entry.cn.value)
                if hasattr(entry, "mail") and entry.mail.value:
                    email = str(entry.mail.value)

            logger.info(f"LDAP Authentication SUCCESS for user: {request.username}")
            return {
                "authenticated": True,
                "username": request.username,
                "displayName": display_name,
                "email": email,
                "dn": user_dn,
                "message": "LDAP authentication successful.",
            }

        logger.warning(f"LDAP Authentication FAILED for user: {request.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password.",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"LDAP connection error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"LDAP Directory error: {str(e)}",
        )
    finally:
        try:
            connection.unbind()
        except Exception:
            pass
