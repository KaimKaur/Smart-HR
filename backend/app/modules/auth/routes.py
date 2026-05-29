from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.schemas import SuccessResponse
from app.core.security import CurrentUser, get_current_user
from app.modules.auth.controller import AuthController
from app.modules.auth.schema import (
    ForgotPasswordRequest,
    LoginRequest,
    MeResponse,
    RefreshRequest,
    ResetPasswordRequest,
    TokenData,
)

router = APIRouter()


def _controller(session: AsyncSession = Depends(get_db)) -> AuthController:
    return AuthController(session)


@router.post("/login", response_model=SuccessResponse[TokenData])
async def login(
    body: LoginRequest,
    request: Request,
    controller: AuthController = Depends(_controller),
) -> SuccessResponse[TokenData]:
    return await controller.login(body, request)


@router.post("/refresh", response_model=SuccessResponse[TokenData])
async def refresh(
    body: RefreshRequest,
    request: Request,
    controller: AuthController = Depends(_controller),
) -> SuccessResponse[TokenData]:
    return await controller.refresh(body, request)


@router.post("/logout", status_code=204)
async def logout(
    request: Request,
    current_user: CurrentUser = Depends(get_current_user),
    controller: AuthController = Depends(_controller),
) -> Response:
    return await controller.logout(current_user, request)


@router.post("/forgot-password")
async def forgot_password(
    body: ForgotPasswordRequest,
    controller: AuthController = Depends(_controller),
) -> SuccessResponse[dict]:
    return await controller.forgot_password(body)


@router.post("/reset-password", response_model=SuccessResponse[None])
async def reset_password(
    body: ResetPasswordRequest,
    controller: AuthController = Depends(_controller),
) -> SuccessResponse[None]:
    return await controller.reset_password(body)


@router.get("/me", response_model=SuccessResponse[MeResponse])
async def me(
    current_user: CurrentUser = Depends(get_current_user),
    controller: AuthController = Depends(_controller),
) -> SuccessResponse[MeResponse]:
    return await controller.me(current_user)
