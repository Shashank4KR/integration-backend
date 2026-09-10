from app.api.v1.finance.fees import (
    accountant_fee_router,
    fee_invoice_router,
    fee_structure_router,
    payment_router,
    student_fee_router,
)
from app.api.v1.finance.finance import finance_router

__all__ = [
    "fee_structure_router",
    "fee_invoice_router",
    "payment_router",
    "student_fee_router",
    "accountant_fee_router",
    "finance_router",
]
