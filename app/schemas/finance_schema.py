from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ExpenseCategoryCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    description: str | None = None
    is_active: bool = True


class ExpenseCategoryUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=100)
    description: str | None = None
    is_active: bool | None = None


class ExpenseCategoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    name: str
    description: str | None = None
    is_active: bool
    created_at: datetime
    updated_at: datetime


class ExpenseCreate(BaseModel):
    category: str = Field(min_length=1, max_length=100)
    expense_category_id: UUID | None = None
    amount: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    expense_date: date
    description: str | None = None
    payment_method: str = "CASH"
    status: str = "PAID"
    reference_no: str | None = None
    approved_by: UUID | None = None
    approval_status: str = "APPROVED"
    attachment_path: str | None = None
    created_by: UUID | None = None


class ExpenseUpdate(BaseModel):
    category: str | None = Field(None, min_length=1, max_length=100)
    expense_category_id: UUID | None = None
    amount: Decimal | None = Field(None, gt=0, max_digits=12, decimal_places=2)
    expense_date: date | None = None
    description: str | None = None
    payment_method: str | None = None
    status: str | None = None
    reference_no: str | None = None
    approved_by: UUID | None = None
    approval_status: str | None = None
    attachment_path: str | None = None
    created_by: UUID | None = None


class ExpenseResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    category: str
    expense_category_id: UUID | None = None
    amount: Decimal
    expense_date: date
    description: str | None = None
    payment_method: str
    status: str
    reference_no: str | None = None
    approved_by: UUID | None = None
    approval_status: str
    attachment_path: str | None = None
    created_by: UUID | None = None
    created_at: datetime
    updated_at: datetime


class SalaryCreate(BaseModel):
    employee_name: str = Field(min_length=1, max_length=255)
    employee_id: str | None = None
    amount: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    month: int = Field(ge=1, le=12)
    year: int
    payment_method: str = "BANK_TRANSFER"
    status: str = "PENDING"
    payment_date: date | None = None
    approved_by: UUID | None = None
    approval_status: str = "APPROVED"
    attachment_path: str | None = None
    created_by: UUID | None = None


class SalaryUpdate(BaseModel):
    employee_name: str | None = Field(None, min_length=1, max_length=255)
    employee_id: str | None = None
    amount: Decimal | None = Field(None, gt=0, max_digits=12, decimal_places=2)
    month: int | None = Field(None, ge=1, le=12)
    year: int | None = None
    payment_method: str | None = None
    status: str | None = None
    payment_date: date | None = None
    approved_by: UUID | None = None
    approval_status: str | None = None
    attachment_path: str | None = None
    created_by: UUID | None = None


class SalaryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    employee_name: str
    employee_id: str | None = None
    amount: Decimal
    month: int
    year: int
    payment_method: str
    status: str
    payment_date: date | None = None
    approved_by: UUID | None = None
    approval_status: str
    attachment_path: str | None = None
    created_by: UUID | None = None
    created_at: datetime
    updated_at: datetime


class StudentCategoryCreate(BaseModel):
    category_name: str = Field(min_length=1, max_length=100)
    description: str | None = None
    discount_percentage: Decimal = Field(ge=0, max_digits=5, decimal_places=2)
    is_active: bool = True


class StudentCategoryUpdate(BaseModel):
    category_name: str | None = Field(None, min_length=1, max_length=100)
    description: str | None = None
    discount_percentage: Decimal | None = Field(None, ge=0, max_digits=5, decimal_places=2)
    is_active: bool | None = None


class StudentCategoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    category_name: str
    description: str | None = None
    discount_percentage: Decimal
    is_active: bool
    created_at: datetime
    updated_at: datetime


class ScholarshipTypeCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: str | None = None
    type: str = "PERCENTAGE"
    value: Decimal = Field(gt=0, max_digits=10, decimal_places=2)
    approval_required: bool = True
    is_active: bool = True
    criteria: str | None = None


class ScholarshipTypeUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
    type: str | None = None
    value: Decimal | None = Field(None, gt=0, max_digits=10, decimal_places=2)
    approval_required: bool | None = None
    is_active: bool | None = None
    criteria: str | None = None


class ScholarshipTypeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    name: str
    description: str | None = None
    type: str
    value: Decimal
    approval_required: bool
    is_active: bool
    criteria: str | None = None
    created_at: datetime
    updated_at: datetime


class StudentScholarshipCreate(BaseModel):
    student_id: UUID
    scholarship_type_id: UUID
    academic_year: str
    scholarship_amount: Decimal = Field(ge=0, max_digits=12, decimal_places=2)
    approved_amount: Decimal | None = Field(None, ge=0, max_digits=12, decimal_places=2)
    approved_by: UUID | None = None
    approval_date: datetime | None = None
    status: str | None = None
    reason: str | None = None


class StudentScholarshipUpdate(BaseModel):
    scholarship_amount: Decimal | None = Field(None, ge=0, max_digits=12, decimal_places=2)
    approved_amount: Decimal | None = Field(None, ge=0, max_digits=12, decimal_places=2)
    approved_by: UUID | None = None
    approval_date: datetime | None = None
    status: str | None = None
    reason: str | None = None


class StudentScholarshipResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    student_id: UUID
    scholarship_type_id: UUID
    scholarship_type_name: str | None = None
    academic_year: str
    scholarship_amount: Decimal
    approved_amount: Decimal | None = None
    approved_by: UUID | None = None
    approval_date: datetime | None = None
    status: str
    reason: str | None = None
    created_at: datetime
    updated_at: datetime


class LateFeeRuleCreate(BaseModel):
    fee_structure_id: UUID | None = None
    name: str = Field(min_length=1, max_length=255)
    type: str = "FIXED"
    value: Decimal = Field(gt=0, max_digits=10, decimal_places=2)
    grace_period_days: int = Field(ge=0)
    applicable_after_days: int = Field(ge=0)
    is_active: bool = True


class LateFeeRuleUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=255)
    type: str | None = None
    value: Decimal | None = Field(None, gt=0, max_digits=10, decimal_places=2)
    grace_period_days: int | None = Field(None, ge=0)
    applicable_after_days: int | None = Field(None, ge=0)
    is_active: bool | None = None


class LateFeeRuleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    fee_structure_id: UUID | None = None
    name: str
    type: str
    value: Decimal
    grace_period_days: int
    applicable_after_days: int
    is_active: bool
    created_at: datetime
    updated_at: datetime


class RefundRequestCreate(BaseModel):
    student_id: UUID
    payment_id: UUID | None = None
    invoice_id: UUID | None = None
    amount: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    reason: str = Field(min_length=1)
    created_by: UUID
    status: str | None = None


class RefundRequestUpdate(BaseModel):
    amount: Decimal | None = Field(None, gt=0, max_digits=12, decimal_places=2)
    reason: str | None = Field(None, min_length=1)
    status: str | None = None
    approved_by: UUID | None = None
    approval_date: datetime | None = None
    processed_date: datetime | None = None
    transaction_no: str | None = None


class RefundRequestResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    student_id: UUID
    payment_id: UUID | None = None
    invoice_id: UUID | None = None
    amount: Decimal
    reason: str
    status: str
    approved_by: UUID | None = None
    approval_date: datetime | None = None
    processed_date: datetime | None = None
    transaction_no: str | None = None
    created_by: UUID
    created_at: datetime
    updated_at: datetime


class OtherIncomeCreate(BaseModel):
    category: str = Field(min_length=1, max_length=100)
    amount: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    income_date: date = Field(...)
    description: str | None = None
    payment_method: str = "CASH"
    reference_no: str | None = None
    received_from: str | None = None
    created_by: UUID | None = None


class OtherIncomeUpdate(BaseModel):
    category: str | None = Field(None, min_length=1, max_length=100)
    amount: Decimal | None = Field(None, gt=0, max_digits=12, decimal_places=2)
    income_date: date | None = None
    description: str | None = None
    payment_method: str | None = None
    reference_no: str | None = None
    received_from: str | None = None
    created_by: UUID | None = None


class OtherIncomeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    category: str
    amount: Decimal
    income_date: date
    description: str | None = None
    payment_method: str
    reference_no: str | None = None
    received_from: str | None = None
    created_by: UUID | None = None
    created_at: datetime
    updated_at: datetime


class FinanceSummaryResponse(BaseModel):
    fee_expected: float
    fee_collected: float
    outstanding: float
    total_expenses: float
    total_income: float
    total_other_income: float
    total_salary: float


class FinanceBalanceResponse(BaseModel):
    bank_balance: float
    cash_in_hand: float
    total_assets: float
    total_liabilities: float
    net_balance: float


class OutstandingSummaryResponse(BaseModel):
    total_students: int
    students_with_outstanding: int
    outstanding_percentage: str
    total_outstanding_amount: str


class FinanceOverviewResponse(BaseModel):
    summary: FinanceSummaryResponse
    balance: FinanceBalanceResponse
    outstanding_summary: OutstandingSummaryResponse


class FinanceTransaction(BaseModel):
    id: str
    receipt_ref_no: str
    date: str
    student_name: str
    class_grade: str
    type: str
    fee_type: str | None = None
    amount: float
    payment_mode: str
    status: str


class FinanceTransactionListResponse(BaseModel):
    items: list[FinanceTransaction]
    total: int


class AdminDashboardResponse(BaseModel):
    today_collection: float
    monthly_collection: float
    pending_fees: float
    overdue_fees: float
    total_revenue: float
    expenses: float
    net_revenue: float
    total_students: int
    students_with_outstanding: int
    top_outstanding_students: list[dict]
    recent_transactions: list[dict]
    payment_methods: list[dict]
    collection_trend: list[dict]


class StudentDashboardResponse(BaseModel):
    invoices: list[dict]
    payment_history: list[dict]
    outstanding_amount: float
    upcoming_due_dates: list[dict]
    scholarship_amount: float
    fine_amount: float
    installments: list[dict]


class ParentDashboardResponse(BaseModel):
    children: list[dict]
    invoices: list[dict]
    receipts: list[dict]
    outstanding_amount: float
    payment_status: list[dict]


class ReceiptResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    receipt_number: str
    transaction_id: str | None = None
    issued_date: str
    student_details: dict
    fee_breakdown: list[dict]
    taxes: list[dict]
    discount: float
    payment_mode: str
    amount_paid: float
    balance_remaining: float
    school_details: dict


class InvoiceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    invoice_number: str
    invoice_date: str
    due_date: str
    status: str
    student_details: dict
    fee_breakdown: list[dict]
    discount_amount: float
    tax_amount: float
    late_fee_amount: float
    scholarship_amount: float
    total_amount: float
    paid_amount: float
    balance_remaining: float


class ReportPaginationParams(BaseModel):
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=500)
    start_date: date | None = None
    end_date: date | None = None
    class_id: UUID | None = None
    section: str | None = None
    student_id: UUID | None = None


class BulkAssignFeeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    student_ids: list[UUID] = Field(..., min_length=1)
    fee_structure_id: UUID
    academic_year: str | None = Field(None, max_length=20)
    due_date: date | None = None


class ScholarshipApproveRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    approved_amount: Decimal | None = Field(None, ge=0)
    approval_date: datetime | None = None


class ScholarshipRejectRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    reason: str | None = Field(None, max_length=500)


class RefundApproveRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    approval_date: datetime | None = None


class RefundProcessRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    processed_date: datetime | None = None
    transaction_no: str | None = Field(None, max_length=100)


class RefundRejectRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    reason: str | None = Field(None, max_length=500)
