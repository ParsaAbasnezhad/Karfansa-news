"""Application-level exceptions translated to a uniform JSON error envelope."""


class AppError(Exception):
    """Base class for expected, client-facing errors."""

    status_code: int = 400
    code: str = "bad_request"
    message: str = "The request could not be processed."

    def __init__(self, message: str | None = None, *, details: object | None = None) -> None:
        self.message = message or self.message
        self.details = details
        super().__init__(self.message)


class NotFoundError(AppError):
    status_code = 404
    code = "not_found"
    message = "The requested resource was not found."


class ConflictError(AppError):
    status_code = 409
    code = "conflict"
    message = "The request conflicts with the current state of the resource."


class RateLimitedError(AppError):
    status_code = 429
    code = "rate_limited"
    message = "Too many requests."
