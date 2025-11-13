import base64
from fastapi import Depends, Request, HTTPException
from jose import jwt
from app.schemas import CurrentUser

# Decode token accepting either unsigned JWT or base64 JSON (for dev convenience)
def _decode_token(token: str) -> dict:
    try:
        if token.count('.') == 2:
            return jwt.get_unverified_claims(token)
        data = base64.b64decode(token).decode()
        import json
        return json.loads(data)
    except Exception as e:
        raise HTTPException(401, f"Invalid token: {e}")

async def get_current_user(req: Request) -> CurrentUser:
    authz = req.headers.get("Authorization") or req.headers.get("authorization")
    if not authz or not authz.startswith("Bearer "):
        raise HTTPException(401, "Missing bearer token")
    token = authz[len("Bearer ") :].strip()
    claims = _decode_token(token)
    for key in ("sub","email","role"):
        if key not in claims:
            raise HTTPException(401, "Bad token claims")
    return CurrentUser(id=claims["sub"], email=claims["email"], role=claims["role"])

# RBAC helpers

def require_role(allowed: list[str]):
    async def _inner(user: CurrentUser = Depends(get_current_user)):
        if user.role not in allowed:
            raise HTTPException(403, "Forbidden")
        return user
    return _inner

def write_guard(user: CurrentUser):
    if user.role in ("support","moderator"):
        raise HTTPException(403, "Read-only role")