from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.core.security import verify_token, User
from app.db.session import get_db

# 重新导出 get_db
__all__ = ["get_current_user", "get_current_active_user", "get_db"]

# 使用 HTTPBearer 替代 OAuth2PasswordBearer
security = HTTPBearer(description="输入你的 access token（不需要 Bearer 前缀）")

# 模拟用户数据库
fake_users_db = {
    "admin": {
        "username": "admin",
        "full_name": "Administrator",
        "email": "admin@example.com",
        "hashed_password": "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",  # "secret"
        "disabled": False,
    }
}


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> User:
    """获取当前用户"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无效的认证凭据",
        headers={"WWW-Authenticate": "Bearer"},
    )

    token_data = verify_token(credentials.credentials)
    if token_data is None:
        raise credentials_exception

    user = fake_users_db.get(token_data.username)
    if user is None:
        raise credentials_exception

    return User(**user)


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """获取当前活跃用户"""
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="用户已禁用")
    return current_user
