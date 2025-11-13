from fastapi import Depends, HTTPException
from app.core.auth import get_current_user, CurrentUser

def require_role(allowed: list[str]):
    async def _inner(user: CurrentUser = Depends(get_current_user)):
        if user.role not in allowed:
            raise HTTPException(403, "Forbidden")
        return user
    return _inner

def write_guard(user: CurrentUser):
    if user.role in ("support","moderator"):
        raise HTTPException(403, "Read-only role")