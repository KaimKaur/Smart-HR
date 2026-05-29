from uuid import UUID

from fastapi import HTTPException, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.schemas import SuccessResponse
from app.core.security import CurrentUser
from app.modules.auth.errors import AuthError
from app.modules.auth.schema import (
    ForgotPasswordRequest,
    LoginRequest,
    MeResponse,
    RefreshRequest,
    ResetPasswordRequest,
    TokenData,
)
from app.modules.auth.service import AuthService


def _client_ip(request: Request) -> str:
    if request.client and request.client.host:
        return request.client.host
    return "0.0.0.0"


class AuthController:
    def __init__(self, session: AsyncSession) -> None:
        self._service = AuthService(session)

    async def login(
        self,
        body: LoginRequest,
        request: Request,
    ) -> SuccessResponse[TokenData]:
        try:
            result = await self._service.login(
                body.email,
                body.password,
                ip_address=_client_ip(request),
            )
        except AuthError as exc:
            raise _auth_http_exception(exc) from exc
        return SuccessResponse(message="Login successful", data=TokenData(**result.model_dump()))

    async def refresh(
        self,
        body: RefreshRequest,
        request: Request,
    ) -> SuccessResponse[TokenData]:
        try:
            result = await self._service.refresh_tokens(
                body.refresh_token,
                ip_address=_client_ip(request),
            )
        except AuthError as exc:
            raise _auth_http_exception(exc) from exc
        return SuccessResponse(
            message="Token refreshed",
            data=TokenData(**result.model_dump()),
        )

    async def logout(self, current_user: CurrentUser, request: Request) -> Response:
        try:
            await self._service.logout(
                current_user.id,
                ip_address=_client_ip(request),
            )
        except AuthError as exc:
            raise _auth_http_exception(exc) from exc
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    async def forgot_password(
        self,
        body: ForgotPasswordRequest,
    ) -> SuccessResponse[dict]:
        data = await self._service.forgot_password_with_token(body.email)
        return SuccessResponse(
            message=(
                "If an account exists for this email, password reset instructions "
                "have been sent."
            ),
            data=data.model_dump(),
        )

    async def reset_password(
        self,
        body: ResetPasswordRequest,
    ) -> SuccessResponse[None]:
        try:
            await self._service.reset_password(body.token, body.new_password)
        except AuthError as exc:
            raise _auth_http_exception(exc) from exc
        return SuccessResponse(message="Password reset successful", data=None)

    async def me(self, current_user: CurrentUser) -> SuccessResponse[MeResponse]:
        try:
            profile = await self._service.get_me(current_user.id)
        except AuthError as exc:
            raise _auth_http_exception(exc) from exc
        return SuccessResponse(message="OK", data=profile)


def _auth_http_exception(exc: AuthError) -> HTTPException:
    return HTTPException(
        status_code=exc.status_code,
        detail={"message": exc.message, "errors": []},
    )
