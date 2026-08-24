from enum import Enum


class UserRole(str, Enum):
    STUDENT = "student"
    OPERATOR = "operator"
    ADMIN = "admin"


class UserStatus(str, Enum):
    ACTIVE = "active"
    DISABLED = "disabled"


class BorrowApplicationStatus(str, Enum):
    SUBMITTED = "submitted"
    APPROVED = "approved"
    PICKED_UP = "picked_up"
    RETURN_PENDING = "return_pending"
    RETURNED = "returned"
    REJECTED = "rejected"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


ACTIVE_RESERVATION_STATUSES = {
    BorrowApplicationStatus.APPROVED.value,
}

TERMINAL_APPLICATION_STATUSES = {
    BorrowApplicationStatus.RETURNED.value,
    BorrowApplicationStatus.REJECTED.value,
    BorrowApplicationStatus.CANCELLED.value,
    BorrowApplicationStatus.EXPIRED.value,
}

INVENTORY_ACTIONS = {"borrow", "return", "transfer", "inbound"}

