import pytest


def test_finance_service_module_imports():
    from app.services import finance_service

    assert hasattr(finance_service, "FinanceService")
    assert hasattr(finance_service, "expense_repository")
    assert hasattr(finance_service, "salary_repository")


def test_finance_service_has_required_methods():
    from app.services.finance_service import FinanceService

    assert hasattr(FinanceService, "get_finance_overview")
    assert hasattr(FinanceService, "get_transactions")
    assert hasattr(FinanceService, "get_expenses")
    assert hasattr(FinanceService, "create_expense")
    assert hasattr(FinanceService, "get_salaries")
    assert hasattr(FinanceService, "create_salary")


def test_finance_service_has_report_methods():
    from app.services.finance_service import FinanceService

    assert hasattr(FinanceService, "get_report_daily_collection")
    assert hasattr(FinanceService, "get_report_monthly_collection")
    assert hasattr(FinanceService, "get_report_yearly_collection")
    assert hasattr(FinanceService, "get_report_outstanding_fees")
    assert hasattr(FinanceService, "get_report_income")
    assert hasattr(FinanceService, "get_report_expense")
    assert hasattr(FinanceService, "get_report_profit_loss")
    assert hasattr(FinanceService, "get_report_payment_mode")
    assert hasattr(FinanceService, "get_report_class_wise_collection")
    assert hasattr(FinanceService, "get_report_section_wise_collection")


def test_finance_service_has_dashboard_methods():
    from app.services.finance_service import FinanceService

    assert hasattr(FinanceService, "get_admin_dashboard")
    assert hasattr(FinanceService, "get_student_dashboard")
    assert hasattr(FinanceService, "get_parent_dashboard")


def test_finance_service_has_receipt_methods():
    from app.services.finance_service import FinanceService

    assert hasattr(FinanceService, "generate_receipt")
    assert hasattr(FinanceService, "generate_invoice")


def test_finance_service_has_integration_methods():
    from app.services.finance_service import FinanceService

    assert hasattr(FinanceService, "get_report_hostel_fee")
    assert hasattr(FinanceService, "get_report_library_fine")
    assert hasattr(FinanceService, "get_report_student_ledger")
    assert hasattr(FinanceService, "get_report_transport_fee")


def test_finance_service_instances_exist():
    from app.services.finance_service import (
        expense_category_service,
        fee_installment_service,
        finance_service,
        late_fee_rule_service,
        other_income_service,
        refund_service,
        salary_service,
        scholarship_type_service,
        student_category_service,
        student_fee_assignment_service,
        student_ledger_service,
        student_scholarship_service,
    )

    assert finance_service is not None
    assert expense_category_service is not None
    assert fee_installment_service is not None
    assert student_fee_assignment_service is not None
    assert student_ledger_service is not None
    assert scholarship_type_service is not None
    assert student_scholarship_service is not None
    assert late_fee_rule_service is not None
    assert refund_service is not None
    assert other_income_service is not None
    assert salary_service is not None


def test_fee_service_has_new_methods():
    from app.services.fee_service import FeeStructureService, FeeInvoiceService, PaymentService

    assert hasattr(FeeStructureService, "get_by_academic_year")
    assert hasattr(FeeInvoiceService, "get_by_student")
    assert hasattr(FeeInvoiceService, "get_unpaid_invoices")
    assert hasattr(FeeInvoiceService, "get_overdue")
    assert hasattr(FeeInvoiceService, "assign_fee_to_student")
    assert hasattr(FeeInvoiceService, "get_student_fee_summary")
    assert hasattr(PaymentService, "get_by_student")
    assert hasattr(PaymentService, "get_by_date_range")
    assert hasattr(PaymentService, "total_paid")
    assert hasattr(PaymentService, "get_revenue_by_month")


def test_finance_repositories_exist():
    from app.repositories.finance_repository import (
        expense_category_repository,
        fee_installment_repository,
        late_fee_rule_repository,
        other_income_repository,
        refund_request_repository,
        student_category_repository,
        student_fee_assignment_repository,
        student_ledger_repository,
        scholarship_type_repository,
        student_scholarship_repository,
    )

    assert student_category_repository is not None
    assert fee_installment_repository is not None
    assert student_fee_assignment_repository is not None
    assert student_ledger_repository is not None
    assert scholarship_type_repository is not None
    assert student_scholarship_repository is not None
    assert late_fee_rule_repository is not None
    assert refund_request_repository is not None
    assert other_income_repository is not None
    assert expense_category_repository is not None


def test_finance_schemas_exist():
    from app.schemas.fee_schema import (
        FeeInstallmentCreate,
        FeeInstallmentResponse,
        FeeInstallmentUpdate,
        StudentFeeAssignmentResponse,
        StudentLedgerResponse,
    )
    from app.schemas.finance_schema import (
        AdminDashboardResponse,
        ExpenseCategoryCreate,
        ExpenseCategoryResponse,
        ExpenseCreate,
        ExpenseResponse,
        FinanceOverviewResponse,
        InvoiceResponse,
        LateFeeRuleCreate,
        LateFeeRuleResponse,
        OtherIncomeCreate,
        OtherIncomeResponse,
        ParentDashboardResponse,
        ReceiptResponse,
        RefundRequestCreate,
        RefundRequestResponse,
        ScholarshipTypeCreate,
        ScholarshipTypeResponse,
        StudentCategoryCreate,
        StudentCategoryResponse,
        StudentDashboardResponse,
        StudentScholarshipCreate,
        StudentScholarshipResponse,
    )

    assert StudentCategoryResponse is not None
    assert FeeInstallmentResponse is not None
    assert StudentFeeAssignmentResponse is not None
    assert StudentLedgerResponse is not None
    assert ScholarshipTypeResponse is not None
    assert StudentScholarshipResponse is not None
    assert LateFeeRuleResponse is not None
    assert RefundRequestResponse is not None
    assert OtherIncomeResponse is not None
    assert ExpenseCategoryResponse is not None
    assert AdminDashboardResponse is not None
    assert StudentDashboardResponse is not None
    assert ParentDashboardResponse is not None
    assert ReceiptResponse is not None
    assert InvoiceResponse is not None
    assert FinanceOverviewResponse is not None


def test_finance_router_has_expected_routes():
    from app.api.v1.finance import finance_router

    route_paths = [route.path for route in finance_router.routes if hasattr(route, "path")]
    expected_routes = [
        "/overview",
        "/transactions",
        "/expenses",
        "/salary",
        "/fee-structures",
        "/invoices",
        "/student-categories",
        "/fee-installments",
        "/student-fee-assignments",
        "/ledgers/{student_id}",
        "/scholarship-types",
        "/scholarships",
        "/late-fee-rules",
        "/refunds",
        "/incomes",
        "/expense-categories",
        "/reports/daily-collection",
        "/reports/monthly-collection",
        "/reports/yearly-collection",
        "/reports/outstanding-fees",
        "/reports/student-ledger",
        "/reports/income-report",
        "/reports/expense-report",
        "/reports/profit-loss",
        "/reports/payment-mode",
        "/reports/class-wise-collection",
        "/reports/section-wise-collection",
        "/reports/hostel-fee",
        "/reports/library-fine",
        "/reports/transport-fee",
        "/receipts/{payment_id}",
        "/invoices/{invoice_id}/pdf",
        "/dashboard/admin",
        "/dashboard/student/{student_id}",
        "/dashboard/parent/{parent_id}",
        "/payments",
    ]
    for route in expected_routes:
        assert route in route_paths, f"Missing route: {route}"


def test_admission_service_integrates_fee_on_approval():
    from app.services.admission_service import AdmissionApplicationService

    assert hasattr(AdmissionApplicationService, "approve_application")


def test_finance_models_importable():
    from app.models.finance_model import (
        Expense,
        ExpenseCategory,
        FeeInstallment,
        LateFeeRule,
        OtherIncome,
        RefundRequest,
        Salary,
        ScholarshipType,
        StudentCategory,
        StudentFeeAssignment,
        StudentLedger,
        StudentScholarship,
    )

    assert StudentCategory is not None
    assert FeeInstallment is not None
    assert StudentFeeAssignment is not None
    assert StudentLedger is not None
    assert ScholarshipType is not None
    assert StudentScholarship is not None
    assert LateFeeRule is not None
    assert RefundRequest is not None
    assert OtherIncome is not None
    assert ExpenseCategory is not None


@pytest.mark.asyncio
async def test_generate_invoice():
    from unittest.mock import AsyncMock, MagicMock
    from uuid import uuid4
    from datetime import date
    from decimal import Decimal
    from app.services.finance_service import finance_service
    from app.services.fee_service import fee_invoice_service

    invoice_id = uuid4()
    mock_invoice = MagicMock()
    mock_invoice.id = invoice_id
    mock_invoice.student_id = uuid4()
    mock_invoice.fee_type_id = uuid4()
    mock_invoice.invoice_number = "INV-12345"
    mock_invoice.invoice_date = date.today()
    mock_invoice.due_date = date.today()
    mock_invoice.status = "PENDING"
    mock_invoice.amount = Decimal("1000.00")
    mock_invoice.net_amount = Decimal("900.00")
    mock_invoice.discount_amount = Decimal("100.00")
    mock_invoice.late_fee_amount = Decimal("0.00")
    mock_invoice.scholarship_amount = Decimal("0.00")

    mock_student = MagicMock()
    mock_student.id = mock_invoice.student_id
    mock_student.first_name = "John"
    mock_student.last_name = "Doe"
    mock_student.class_name = "Grade 10"
    mock_student.admission_no = "ADM123"

    mock_fee_struct = MagicMock()
    mock_fee_struct.fee_type = "Tuition"
    mock_fee_struct.tax_percentage = Decimal("5.00")

    mock_session = AsyncMock()
    mock_session.get.side_effect = [mock_student, mock_fee_struct]

    fee_invoice_service_get_original = fee_invoice_service.get
    fee_invoice_service.get = AsyncMock(return_value=mock_invoice)

    import app.services.finance_service
    original_invoice_total_paid = app.services.finance_service._invoice_total_paid
    app.services.finance_service._invoice_total_paid = AsyncMock(return_value=Decimal("200.00"))

    try:
        result = await finance_service.generate_invoice(mock_session, invoice_id)
        assert result["invoice_number"] == "INV-12345"
        assert result["student_details"]["name"] == "John Doe"
        assert result["fee_breakdown"][0]["fee_type"] == "Tuition"
        assert result["total_amount"] == 900.0
        assert result["paid_amount"] == 200.0
        assert result["balance_remaining"] == 700.0
    finally:
        fee_invoice_service.get = fee_invoice_service_get_original
        app.services.finance_service._invoice_total_paid = original_invoice_total_paid
