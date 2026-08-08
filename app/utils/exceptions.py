"""Application-level exceptions and standard error messages."""

# Common error detail messages
TOKEN_MISSING_DETAIL = "Not authenticated. Missing Bearer token."
INVALID_TOKEN_DETAIL = "Invalid or expired token."
USER_NOT_FOUND_DETAIL = "User not found."
TRANSACTION_NOT_FOUND_DETAIL = "Transaction not found."
UNAUTHORIZED_TRANSACTION_DETAIL = "You are not allowed to access this transaction."
EMAIL_ALREADY_EXISTS_DETAIL = "An account with this email already exists."
INVALID_CREDENTIALS_DETAIL = "Invalid email or password."
AUTH_SERVICE_UNAVAILABLE_DETAIL = "Authentication service is currently unavailable."


class AppError(Exception):
    """Base application error."""

    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class NotFoundError(AppError):
    def __init__(self, message: str = USER_NOT_FOUND_DETAIL):
        super().__init__(message, status_code=404)


class ConflictError(AppError):
    def __init__(self, message: str = "Resource already exists."):
        super().__init__(message, status_code=409)


class ForbiddenError(AppError):
    def __init__(self, message: str = "Forbidden."):
        super().__init__(message, status_code=403)


class UnauthorizedError(AppError):
    def __init__(self, message: str = "Unauthorized."):
        super().__init__(message, status_code=401)


class BadRequestError(AppError):
    def __init__(self, message: str = "Bad request."):
        super().__init__(message, status_code=400)
