"""Schema 层统一导出"""
from app.schemas.auth import (
    RegisterRequest, LoginRequest, UpdateProfileRequest, UpdatePasswordRequest
)
from app.schemas.model import TrainRequest
from app.schemas.email import (
    GenerateEmailRequest, PromptUpdateRequest, EmailUpdateRequest,
    EmailStatusRequest, BatchDeleteRequest
)
