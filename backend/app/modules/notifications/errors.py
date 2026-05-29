class NotificationsError(Exception):
    def __init__(
        self,
        message: str,
        status_code: int = 400,
        *,
        errors: list[dict[str, str]] | None = None,
    ) -> None:
        self.message = message
        self.status_code = status_code
        self.errors = errors or []
        super().__init__(message)

