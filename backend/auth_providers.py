import os
from abc import ABC, abstractmethod
from dataclasses import dataclass

from fastapi import HTTPException

from constants import UserRole
from schemas import AuthLoginRequest


@dataclass
class AuthIdentity:
    external_subject: str
    student_no: str | None
    name: str
    role: str = UserRole.STUDENT.value


class AuthProvider(ABC):
    @abstractmethod
    def authenticate(self, body: AuthLoginRequest) -> AuthIdentity:
        raise NotImplementedError


class MockAuthProvider(AuthProvider):
    def authenticate(self, body: AuthLoginRequest) -> AuthIdentity:
        app_env = os.getenv("APP_ENV", "development").lower()
        enabled = os.getenv("MOCK_AUTH_ENABLED", "false").lower() == "true"
        if app_env == "production" or not enabled:
            raise HTTPException(status_code=403, detail="模拟认证仅允许在开发环境使用")

        role = body.role if body.role in {r.value for r in UserRole} else UserRole.STUDENT.value
        subject = body.external_subject or body.credential or f"mock:{body.student_no or 'student'}"
        return AuthIdentity(
            external_subject=subject,
            student_no=body.student_no,
            name=(body.name or body.student_no or "开发测试学生").strip(),
            role=role,
        )


class SchoolAuthProvider(AuthProvider):
    """Stable adapter boundary for the future campus OAuth/CAS integration."""

    def authenticate(self, body: AuthLoginRequest) -> AuthIdentity:
        raise HTTPException(status_code=503, detail="学校统一认证尚未配置")


def get_auth_provider() -> AuthProvider:
    provider = os.getenv("AUTH_PROVIDER", "mock").lower()
    if provider == "mock":
        return MockAuthProvider()
    if provider == "school":
        return SchoolAuthProvider()
    raise HTTPException(status_code=500, detail=f"不支持的认证适配器: {provider}")

