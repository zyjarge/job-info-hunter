from datetime import timedelta
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status, Form
from app.core.security import (
    Token,
    User,
    create_access_token,
    verify_password,
    ACCESS_TOKEN_EXPIRE_MINUTES,
)
from app.api.deps import fake_users_db, get_current_active_user

router = APIRouter()


@router.post("/token", response_model=Token, summary="获取访问令牌")
async def login_for_access_token(
    username: str = Form(...), password: str = Form(...)
) -> Any:
    """
    获取访问令牌

    - **username**: 用户名（测试账号：admin）
    - **password**: 密码（测试密码：secret）
    """
    user = fake_users_db.get(username)
    if not user or not verify_password(password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["username"]}, expires_delta=access_token_expires
    )

    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/users/me", response_model=User, summary="获取当前用户信息")
async def read_users_me(current_user: User = Depends(get_current_active_user)) -> Any:
    """
    获取当前登录用户的信息

    需要在请求头中携带 token：
    ```
    Authorization: Bearer your_token
    ```
    """
    return current_user
