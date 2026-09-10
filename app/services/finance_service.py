from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.class_model import Class
from app.models.fee_model import (
    FeeInvoice,
    FeeStructure,
    Payment,
)
from app.models.finance_model import (
    Expense,
    ExpenseCategory,
    LateFeeRule,
    OtherIncome,
    RefundRequest,
    RefundStatus,
    Salary,
    ScholarshipType,
    StudentCategory,
    StudentFeeAssignment,
    StudentLedger,
    StudentScholarship,
)
from app.models.student_model import Student
from app.models.user import User
from app.repositories.fee_repository import fee_invoice_repository, payment_repository
from app.repositories.finance_repository import (
    expense_category_repository,
    expense_repository,
    fee_installment_repository,
    late_fee_rule_repository,
    other_income_repository,
    refund_request_repository,
    salary_repository,
    student_category_repository,
    student_fee_assignment_repository,
    student_ledger_repository,
    scholarship_type_repository,
    student_scholarship_repository,
)
from app.services.crud_service import CRUDService
from app.services.fee_service import fee_invoice_service


def _bad_request(detail: str) -> None:
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)


def _not_found(detail: str) -> None:
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


class FinanceService:
    def __init__(self, expense_repo, salary_repo):
        self.expense_repo = expense_repo
        self.salary_repo = salary_repo

    async def get_finance_overview(self, session: AsyncSession) -> dict:
        total_invoiced = await session.scalar(
            select(func.coalesce(func.sum(FeeInvoice.amount), 0))
        ) or 0
        total_paid = await session.scalar(
            select(func.coalesce(func.sum(Payment.amount_paid), 0))
        ) or 0
        total_expenses = await self.expense_repo.total(session) or 0
        total_salary = await self.salary_repo.total(session) or 0
        total_other_income = await other_income_repository.total(session) or 0
        outstanding = float(total_invoiced) - float(total_paid)

        total_students = await session.scalar(select(func.count(Student.id))) or 0

        unpaid_invoices = await session.execute(
            select(func.count(FeeInvoice.id)).where(
                FeeInvoice.status.in_(["UNPAID", "PENDING", "PARTIAL", "OVERDUE"])
            )
        )
        unpaid_count = unpaid_invoices.scalar_one() or 0

        if total_students > 0:
            pct = round((unpaid_count / total_students) * 100, 1)
            outstanding_percentage = f"{pct}%"
        else:
            outstanding_percentage = "0%"

        return {
            "summary": {
                "fee_expected": float(total_invoiced),
                "fee_collected": float(total_paid),
                "outstanding": float(outstanding),
                "total_expenses": float(total_expenses),
                "total_income": float(total_paid) + total_other_income,
                "total_other_income": total_other_income,
                "total_salary": float(total_salary),
            },
            "balance": {
                "bank_balance": float(total_paid)
                + total_other_income
                - float(total_expenses)
                - float(total_salary),
                "cash_in_hand": float(total_expenses) * 0.1,
                "total_assets": float(total_invoiced) + float(total_paid) * 0.5,
                "total_liabilities": float(total_expenses) + float(total_salary),
                "net_balance": float(total_invoiced)
                + float(total_paid) * 0.5
                + total_other_income
                - float(total_expenses)
                - float(total_salary),
            },
            "outstanding_summary": {
                "total_students": total_students,
                "students_with_outstanding": unpaid_count,
                "outstanding_percentage": outstanding_percentage,
                "total_outstanding_amount": f"₹ {float(outstanding):,.2f}",
            },
        }

    async def get_transactions(self, session: AsyncSession) -> list[dict]:
        payment_query = (
            select(Payment, FeeInvoice, FeeStructure, Student)
            .join(FeeInvoice, Payment.invoice_id == FeeInvoice.id)
            .join(FeeStructure, FeeInvoice.fee_type_id == FeeStructure.id)
            .join(Student, FeeInvoice.student_id == Student.id)
            .order_by(Payment.payment_date.desc())
        )
        result = await session.execute(payment_query)
        rows = result.all()

        transactions: list[dict] = []
        for payment, invoice, fee_structure, student in rows:
            full_name = (
                f"{student.first_name or ''} {student.last_name or ''}".strip()
            )
            transactions.append(
                {
                    "id": str(payment.id),
                    "receipt_ref_no": payment.receipt_no
                    or payment.transaction_no
                    or "",
                    "date": payment.payment_date.isoformat()
                    if payment.payment_date
                    else "",
                    "student_name": full_name or "Unknown",
                    "class_grade": student.class_name or "",
                    "type": fee_structure.fee_type or "",
                    "fee_type": fee_structure.fee_type or "",
                    "amount": float(payment.amount_paid),
                    "payment_mode": payment.payment_method or "",
                    "status": "Paid",
                }
            )

        expense_query = (
            select(Expense)
            .where(Expense.category != "salary")
            .order_by(Expense.expense_date.desc())
        )
        expenses = (await session.execute(expense_query)).scalars().all()
        for exp in expenses:
            transactions.append(
                {
                    "id": f"exp-{exp.id}",
                    "receipt_ref_no": exp.reference_no or "",
                    "date": exp.expense_date.isoformat()
                    if exp.expense_date
                    else "",
                    "student_name": "",
                    "class_grade": "",
                    "type": exp.category,
                    "fee_type": exp.category,
                    "amount": float(exp.amount),
                    "payment_mode": exp.payment_method,
                    "status": exp.status,
                }
            )

        other_income_query = select(OtherIncome).order_by(
            OtherIncome.income_date.desc()
        )
        other_incomes = (await session.execute(other_income_query)).scalars().all()
        for inc in other_incomes:
            transactions.append(
                {
                    "id": f"inc-{inc.id}",
                    "receipt_ref_no": inc.reference_no or "",
                    "date": inc.income_date.isoformat()
                    if inc.income_date
                    else "",
                    "student_name": "",
                    "class_grade": "",
                    "type": inc.category,
                    "fee_type": "Other Income",
                    "amount": float(inc.amount),
                    "payment_mode": inc.payment_method,
                    "status": "Received",
                }
            )

        transactions.sort(key=lambda t: t["date"], reverse=True)
        return transactions

    async def get_expenses(self, session: AsyncSession) -> list[Expense]:
        return await self.expense_repo.list(session)

    async def get_expense(self, session: AsyncSession, item_id: UUID) -> Expense:
        item = await self.expense_repo.get(session, item_id)
        if item is None:
            _not_found("Expense not found")
        return item

    async def create_expense(self, session: AsyncSession, data: dict) -> Expense:
        item = Expense(**data)
        session.add(item)
        await session.flush()
        await session.refresh(item)
        await session.commit()
        return item

    async def get_salaries(self, session: AsyncSession) -> list[Salary]:
        return await self.salary_repo.list(session)

    async def create_salary(self, session: AsyncSession, data: dict) -> Salary:
        item = Salary(**data)
        session.add(item)
        await session.flush()
        await session.refresh(item)
        await session.commit()
        return item

    async def get_admin_dashboard(self, session: AsyncSession) -> dict:
        today = date.today()
        month_start = today.replace(day=1)

        total_students = await session.scalar(
            select(func.count(Student.id))
        ) or 0

        today_collection = await payment_repository.total_paid(
            session, start_date=today, end_date=today
        )
        monthly_collection = await payment_repository.total_paid(
            session, start_date=month_start, end_date=today
        )

        outstanding_result = await session.execute(
            select(func.coalesce(func.sum(FeeInvoice.amount), 0)).where(
                FeeInvoice.status.in_(["UNPAID", "PENDING", "PARTIAL", "OVERDUE"])
            )
        )
        pending_fees = float(outstanding_result.scalar_one())

        overdue_invoices = await fee_invoice_repository.get_overdue(session, today)
        overdue_fees = sum(
            float(inv.net_amount if inv.net_amount else inv.amount)
            for inv in overdue_invoices
        )

        total_expenses = float(await self.expense_repo.total(session) or 0)
        total_salary = float(await self.salary_repo.total(session) or 0)
        total_revenue = float(today_collection) + monthly_collection
        net_revenue = total_revenue - total_expenses - total_salary

        recent_payments = await payment_repository.get_by_date_range(
            session, month_start, today
        )
        recent_transactions = []
        for p in recent_payments[-10:]:
            invoice = await session.get(FeeInvoice, p.invoice_id)
            student = await session.get(Student, invoice.student_id) if invoice else None
            recent_transactions.append(
                {
                    "date": p.payment_date.isoformat() if p.payment_date else "",
                    "student_name": f"{student.first_name or ''} {student.last_name or ''}".strip() if student else "Unknown",
                    "amount": float(p.amount_paid),
                    "method": p.payment_method,
                    "receipt": p.receipt_number or p.receipt_no or "",
                }
            )

        payment_method_query = (
            select(Payment.payment_method, func.sum(Payment.amount_paid).label("total"))
            .where(Payment.payment_date >= month_start)
            .group_by(Payment.payment_method)
            .order_by(func.sum(Payment.amount_paid).desc())
        )
        payment_methods_result = await session.execute(payment_method_query)
        payment_methods = [
            {"method": row.payment_method, "total": float(row.total)}
            for row in payment_methods_result.all()
        ]

        revenue_by_month = await payment_repository.get_revenue_by_month(
            session, today.year
        )
        collection_trend = [
            {"month": row["month"], "total": row["total"]}
            for row in revenue_by_month
        ]

        top_outstanding = await session.execute(
            select(Student)
            .join(FeeInvoice, FeeInvoice.student_id == Student.id)
            .where(FeeInvoice.status.in_(["UNPAID", "PENDING", "PARTIAL", "OVERDUE"]))
            .group_by(Student.id)
            .order_by(func.sum(FeeInvoice.amount).desc())
            .limit(5)
        )
        top_students = []
        for student in top_outstanding.scalars().all():
            invoices = await fee_invoice_repository.get_unpaid_invoices(
                session, student.id
            )
            outstanding = sum(
                float(inv.net_amount if inv.net_amount else inv.amount)
                for inv in invoices
            )
            top_students.append(
                {
                    "student_id": str(student.id),
                    "name": f"{student.first_name or ''} {student.last_name or ''}".strip(),
                    "class": student.class_name or "",
                    "outstanding": outstanding,
                }
            )

        return {
            "today_collection": today_collection,
            "monthly_collection": monthly_collection,
            "pending_fees": pending_fees,
            "overdue_fees": overdue_fees,
            "total_revenue": total_revenue,
            "expenses": total_expenses,
            "net_revenue": net_revenue,
            "total_students": total_students,
            "students_with_outstanding": len(top_students),
            "top_outstanding_students": top_students,
            "recent_transactions": recent_transactions,
            "payment_methods": payment_methods,
            "collection_trend": collection_trend,
        }

    async def get_student_dashboard(
        self, session: AsyncSession, student_id: UUID
    ) -> dict:
        student = await session.get(Student, student_id)
        if student is None:
            _not_found("Student not found")

        invoices = await fee_invoice_repository.get_by_student(session, student_id)
        outstanding = Decimal("0.00")
        upcoming_due_dates = []
        for inv in invoices:
            net = inv.net_amount if inv.net_amount is not None else inv.amount
            total_paid = await _invoice_total_paid(session, inv.id)
            balance = net - total_paid
            if balance > 0 and inv.status != "CANCELLED":
                outstanding += balance
            if inv.status in ["UNPAID", "PENDING", "PARTIAL", "OVERDUE"]:
                upcoming_due_dates.append(
                    {
                        "invoice_id": str(inv.id),
                        "invoice_number": inv.invoice_number or "",
                        "due_date": inv.due_date.isoformat() if inv.due_date else "",
                        "amount": float(net),
                        "balance": float(balance),
                        "status": inv.status,
                    }
                )

        payments = await payment_repository.get_by_student(session, student_id)
        payment_history = [
            {
                "payment_id": str(p.id),
                "date": p.payment_date.isoformat() if p.payment_date else "",
                "amount": float(p.amount_paid),
                "method": p.payment_method,
                "receipt": p.receipt_number or p.receipt_no or "",
                "status": p.payment_status,
            }
            for p in payments
        ]

        scholarships = await student_scholarship_repository.get_by_student(
            session, student_id
        )
        scholarship_amount = sum(
            float(s.approved_amount or s.scholarship_amount)
            for s in scholarships
            if s.status == "APPROVED"
        )

        ledger = await student_ledger_repository.get_by_student_and_type(
            session, student_id, "LATE_FEE"
        )
        fine_amount = sum(float(l.debit) for l in ledger)

        return {
            "invoices": [
                {
                    "invoice_id": str(inv.id),
                    "invoice_number": inv.invoice_number or "",
                    "amount": float(inv.net_amount if inv.net_amount else inv.amount),
                    "status": inv.status,
                    "due_date": inv.due_date.isoformat() if inv.due_date else "",
                }
                for inv in invoices
            ],
            "payment_history": payment_history,
            "outstanding_amount": float(outstanding),
            "upcoming_due_dates": upcoming_due_dates,
            "scholarship_amount": scholarship_amount,
            "fine_amount": fine_amount,
            "installments": [],
        }

    async def get_parent_dashboard(
        self, session: AsyncSession, parent_id: UUID
    ) -> dict:
        from app.models.parent_student_model import ParentStudent

        parent_students = await session.execute(
            select(ParentStudent).where(ParentStudent.parent_id == parent_id)
        )
        parent_student_links = parent_students.scalars().all()

        children = []
        total_outstanding = Decimal("0.00")
        all_invoices = []
        all_receipts = []

        for link in parent_student_links:
            student = await session.get(Student, link.student_id)
            if not student:
                continue
            student_outstanding = Decimal("0.00")
            invoices = await fee_invoice_repository.get_by_student(
                session, student.id
            )
            student_invoices = []
            for inv in invoices:
                net = inv.net_amount if inv.net_amount is not None else inv.amount
                total_paid = await _invoice_total_paid(session, inv.id)
                balance = net - total_paid
                if balance > 0 and inv.status != "CANCELLED":
                    student_outstanding += balance
                student_invoices.append(
                    {
                        "invoice_id": str(inv.id),
                        "invoice_number": inv.invoice_number or "",
                        "amount": float(net),
                        "paid": float(total_paid),
                        "balance": float(balance),
                        "status": inv.status,
                        "due_date": inv.due_date.isoformat() if inv.due_date else "",
                    }
                )
            all_invoices.extend(student_invoices)
            total_outstanding += student_outstanding

            payments = await payment_repository.get_by_student(
                session, student.id
            )
            for p in payments:
                all_receipts.append(
                    {
                        "receipt_id": str(p.id),
                        "receipt_number": p.receipt_number or p.receipt_no or "",
                        "date": p.payment_date.isoformat() if p.payment_date else "",
                        "amount": float(p.amount_paid),
                        "method": p.payment_method,
                        "student_name": f"{student.first_name or ''} {student.last_name or ''}".strip(),
                    }
                )

            children.append(
                {
                    "student_id": str(student.id),
                    "name": f"{student.first_name or ''} {student.last_name or ''}".strip(),
                    "admission_no": student.admission_no,
                    "outstanding": float(student_outstanding),
                    "invoices": student_invoices,
                }
            )

        payment_status = [
            {"status": "Paid", "count": len([i for i in all_invoices if i["status"] == "PAID"])},
            {"status": "Pending", "count": len([i for i in all_invoices if i["status"] in ["UNPAID", "PENDING"]])},
            {"status": "Overdue", "count": len([i for i in all_invoices if i["status"] == "OVERDUE"])},
            {"status": "Partial", "count": len([i for i in all_invoices if i["status"] == "PARTIAL"])},
        ]

        return {
            "children": children,
            "invoices": all_invoices,
            "receipts": all_receipts,
            "outstanding_amount": float(total_outstanding),
            "payment_status": payment_status,
        }

    async def get_report_daily_collection(
        self, session: AsyncSession, report_date: date | None = None
    ) -> dict:
        target_date = report_date or date.today()
        start = target_date
        end = target_date

        payments = await payment_repository.get_by_date_range(session, start, end)
        total = sum(float(p.amount_paid) for p in payments)
        by_method: dict[str, float] = {}
        for p in payments:
            by_method[p.payment_method] = by_method.get(p.payment_method, 0.0) + float(
                p.amount_paid
            )

        return {
            "date": target_date.isoformat(),
            "total_collection": total,
            "total_transactions": len(payments),
            "by_method": by_method,
            "transactions": [
                {
                    "id": str(p.id),
                    "student_id": str((await session.get(FeeInvoice, p.invoice_id)).student_id) if await session.get(FeeInvoice, p.invoice_id) else "",
                    "amount": float(p.amount_paid),
                    "method": p.payment_method,
                    "receipt": p.receipt_number or p.receipt_no or "",
                }
                for p in payments
            ],
        }

    async def get_report_monthly_collection(
        self, session: AsyncSession, year: int | None = None, month: int | None = None
    ) -> dict:
        today = date.today()
        year = year or today.year
        month = month or today.month
        start = date(year, month, 1)
        end = date(year, month, 28) if month != 2 else date(year, month, 29)
        end = min(end, date(year, month, 31))

        total = await payment_repository.total_paid(session, start_date=start, end_date=end)
        payments = await payment_repository.get_by_date_range(session, start, end)
        by_method: dict[str, float] = {}
        for p in payments:
            by_method[p.payment_method] = by_method.get(p.payment_method, 0.0) + float(
                p.amount_paid
            )

        return {
            "year": year,
            "month": month,
            "total_collection": total,
            "total_transactions": len(payments),
            "by_method": by_method,
        }

    async def get_report_yearly_collection(
        self, session: AsyncSession, year: int | None = None
    ) -> dict:
        year = year or date.today().year
        start = date(year, 1, 1)
        end = date(year, 12, 31)

        total = await payment_repository.total_paid(session, start_date=start, end_date=end)
        payments = await payment_repository.get_by_date_range(session, start, end)
        by_method: dict[str, float] = {}
        
        MONTH_NAMES = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        monthly_totals = {m: Decimal("0.00") for m in MONTH_NAMES}

        for p in payments:
            method_key = p.payment_method or "Other"
            by_method[method_key] = by_method.get(method_key, 0.0) + float(p.amount_paid)
            
            p_date = p.payment_date or (p.created_at.date() if p.created_at else None)
            if p_date:
                m_name = MONTH_NAMES[p_date.month - 1]
                monthly_totals[m_name] += p.amount_paid

        monthly_breakdown = [
            {"month": m, "total": float(amt)}
            for m, amt in monthly_totals.items()
        ]

        return {
            "year": year,
            "total_collection": total,
            "total_transactions": len(payments),
            "by_method": by_method,
            "monthly_breakdown": monthly_breakdown,
        }

    async def get_report_outstanding_fees(
        self, session: AsyncSession, class_id: UUID | None = None, section: str | None = None
    ) -> dict:
        query = (
            select(FeeInvoice, Student, FeeStructure)
            .join(Student, FeeInvoice.student_id == Student.id)
            .join(FeeStructure, FeeInvoice.fee_type_id == FeeStructure.id)
            .where(FeeInvoice.status.in_(["UNPAID", "PENDING", "PARTIAL", "OVERDUE"]))
        )
        if class_id is not None:
            query = query.where(Student.class_id == class_id)
        if section is not None:
            query = query.where(Student.class_name == section)
        result = await session.execute(query)
        rows = result.all()

        total_outstanding = Decimal("0.00")
        students_outstanding: dict[UUID, dict] = {}
        for inv, student, fee_struct in rows:
            net = inv.net_amount if inv.net_amount is not None else inv.amount
            total_paid = await _invoice_total_paid(session, inv.id)
            balance = net - total_paid
            total_outstanding += balance
            sid = student.id
            if sid not in students_outstanding:
                students_outstanding[sid] = {
                    "student_id": str(sid),
                    "name": f"{student.first_name or ''} {student.last_name or ''}".strip(),
                    "class": student.class_name or "",
                    "total_outstanding": Decimal("0.00"),
                    "invoices": [],
                }
            students_outstanding[sid]["total_outstanding"] += balance
            students_outstanding[sid]["invoices"].append(
                {
                    "invoice_id": str(inv.id),
                    "fee_type": fee_struct.fee_type,
                    "amount": float(net),
                    "paid": float(total_paid),
                    "balance": float(balance),
                    "status": inv.status,
                    "due_date": inv.due_date.isoformat() if inv.due_date else "",
                }
            )

        return {
            "total_outstanding": float(total_outstanding),
            "total_students": len(students_outstanding),
            "students": list(students_outstanding.values()),
        }

    async def get_report_income(
        self,
        session: AsyncSession,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> dict:
        fee_income = Decimal("0.00")
        if start_date and end_date:
            payments_in_range = await payment_repository.get_by_date_range(
                session, start_date, end_date
            )
            fee_income = sum((p.amount_paid for p in payments_in_range), Decimal("0.00"))

        other_income = Decimal("0.00")
        if start_date and end_date:
            other_income = Decimal(
                str(
                    await other_income_repository.total_by_date_range(
                        session, start_date, end_date
                    )
                )
            )

        return {
            "start_date": start_date.isoformat() if start_date else None,
            "end_date": end_date.isoformat() if end_date else None,
            "fee_income": float(fee_income),
            "other_income": float(other_income),
            "total_income": float(fee_income + other_income),
        }

    async def get_report_expense(
        self,
        session: AsyncSession,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> dict:
        total = Decimal("0.00")
        if start_date and end_date:
            expenses = await expense_repository.get_by_date_range(
                session, start_date, end_date
            )
            total = sum((exp.amount for exp in expenses), Decimal("0.00"))
        else:
            total = Decimal(str(await expense_repository.total(session)))

        by_category = await expense_repository.expenses_by_category(session)
        return {
            "start_date": start_date.isoformat() if start_date else None,
            "end_date": end_date.isoformat() if end_date else None,
            "total_expenses": float(total),
            "by_category": by_category,
        }

    async def get_report_profit_loss(
        self,
        session: AsyncSession,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> dict:
        fee_income = Decimal("0.00")
        other_income = Decimal("0.00")
        if start_date and end_date:
            payments_in_range = await payment_repository.get_by_date_range(
                session, start_date, end_date
            )
            fee_income = sum((p.amount_paid for p in payments_in_range), Decimal("0.00"))
            other_income = Decimal(
                str(
                    await other_income_repository.total_by_date_range(
                        session, start_date, end_date
                    )
                )
            )

        total_expenses = Decimal("0.00")
        if start_date and end_date:
            total_expenses = Decimal(
                str(await expense_repository.sum_by_date_range(session, start_date, end_date))
            )
        else:
            total_expenses = Decimal(str(await expense_repository.total(session)))

        total_salary = Decimal("0.00")
        if start_date and end_date:
            total_salary = Decimal(
                str(await salary_repository.total_by_date_range(session, start_date, end_date))
            )
        else:
            total_salary = Decimal(str(await salary_repository.total(session)))

        gross_profit = fee_income + other_income
        net_profit = gross_profit - total_expenses - total_salary

        return {
            "start_date": start_date.isoformat() if start_date else None,
            "end_date": end_date.isoformat() if end_date else None,
            "fee_income": float(fee_income),
            "other_income": float(other_income),
            "gross_profit": float(gross_profit),
            "expenses": float(total_expenses),
            "salary": float(total_salary),
            "net_profit": float(net_profit),
            "status": "Profit" if net_profit >= 0 else "Loss",
        }

    async def get_report_payment_mode(
        self,
        session: AsyncSession,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> dict:
        query = (
            select(
                Payment.payment_method,
                func.coalesce(func.sum(Payment.amount_paid), 0).label("total"),
            )
            .group_by(Payment.payment_method)
            .order_by(func.sum(Payment.amount_paid).desc())
        )
        if start_date is not None:
            query = query.where(Payment.payment_date >= start_date)
        if end_date is not None:
            query = query.where(Payment.payment_date <= end_date)
        result = await session.execute(query)
        payment_modes = [
            {"method": row.payment_method, "total": float(row.total)}
            for row in result.all()
        ]
        return {
            "start_date": start_date.isoformat() if start_date else None,
            "end_date": end_date.isoformat() if end_date else None,
            "payment_modes": payment_modes,
        }

    async def get_report_class_wise_collection(
        self, session: AsyncSession, academic_year: str | None = None
    ) -> dict:
        classes_result = await session.execute(
            select(Class).where(Class.academic_year == academic_year)
            if academic_year
            else select(Class)
        )
        classes = classes_result.scalars().all()
        class_data = []
        for cls in classes:
            students_in_class = await session.execute(
                select(Student.id).where(Student.class_id == cls.id)
            )
            student_ids = [row[0] for row in students_in_class.all()]
            if not student_ids:
                continue
            invoices_query = (
                select(FeeInvoice)
                .where(FeeInvoice.student_id.in_(student_ids))
                .where(FeeInvoice.status.in_(["PAID", "PARTIAL"]))
            )
            invoices = (await session.execute(invoices_query)).scalars().all()
            collected = sum(
                float(inv.amount) for inv in invoices
            )
            class_data.append(
                {
                    "class_id": str(cls.id),
                    "class_name": cls.class_name,
                    "section": cls.section,
                    "academic_year": cls.academic_year,
                    "total_collected": collected,
                    "student_count": len(student_ids),
                }
            )
        return {"academic_year": academic_year, "classes": class_data}

    async def get_report_section_wise_collection(
        self, session: AsyncSession, academic_year: str | None = None
    ) -> dict:
        sections_query = select(Class.section).distinct()
        if academic_year:
            sections_query = sections_query.where(Class.academic_year == academic_year)
        sections = (await session.execute(sections_query)).scalars().all()

        section_data = []
        for section in sections:
            students_in_section = await session.execute(
                select(Student.id).where(
                    Student.class_name == section,
                    Student.class_id != None,
                )
            )
            student_ids = [row[0] for row in students_in_section.all()]
            if not student_ids:
                continue
            invoices_query = (
                select(FeeInvoice)
                .where(FeeInvoice.student_id.in_(student_ids))
                .where(FeeInvoice.status.in_(["PAID", "PARTIAL"]))
            )
            invoices = (await session.execute(invoices_query)).scalars().all()
            collected = sum(
                float(inv.amount) for inv in invoices
            )
            section_data.append(
                {
                    "section": section,
                    "total_collected": collected,
                    "student_count": len(student_ids),
                }
            )
        return {
            "academic_year": academic_year,
            "sections": section_data,
        }

    async def get_report_hostel_fee(
        self, session: AsyncSession, start_date: date | None = None, end_date: date | None = None
    ) -> dict:
        from app.models.hostel_operations_model import HostelFeeInvoice, HostelPayment

        query = (
            select(HostelFeeInvoice, HostelPayment, Student)
            .join(HostelPayment, HostelPayment.invoice_id == HostelFeeInvoice.id)
            .join(Student, HostelFeeInvoice.student_id == Student.id)
        )
        if start_date:
            query = query.where(HostelPayment.payment_date >= start_date)
        if end_date:
            query = query.where(HostelPayment.payment_date <= end_date)
        result = await session.execute(query)
        rows = result.all()

        total_collected = Decimal("0.00")
        total_pending = Decimal("0.00")
        for inv, payment, student in rows:
            total_collected += payment.amount_paid

        pending_query = select(HostelFeeInvoice).where(
            HostelFeeInvoice.status.in_(["PENDING", "OVERDUE"])
        )
        pending_invoices = (await session.execute(pending_query)).scalars().all()
        total_pending = sum(
            (inv.amount for inv in pending_invoices), Decimal("0.00")
        )

        return {
            "start_date": start_date.isoformat() if start_date else None,
            "end_date": end_date.isoformat() if end_date else None,
            "total_collected": float(total_collected),
            "total_pending": float(total_pending),
        }

    async def get_report_library_fine(
        self, session: AsyncSession, start_date: date | None = None, end_date: date | None = None
    ) -> dict:
        from app.models.library_model import FinePayment, BookIssue

        query = (
            select(FinePayment, BookIssue, Student)
            .join(BookIssue, FinePayment.issue_id == BookIssue.id)
            .join(Student, BookIssue.student_id == Student.id)
        )
        if start_date:
            query = query.where(FinePayment.payment_date >= start_date)
        if end_date:
            query = query.where(FinePayment.payment_date <= end_date)
        result = await session.execute(query)
        rows = result.all()

        total_collected = Decimal("0.00")
        total_pending = Decimal("0.00")
        for fine, issue, student in rows:
            total_collected += fine.amount

        pending_query = select(FinePayment).where(FinePayment.status == "PENDING")
        pending_fines = (await session.execute(pending_query)).scalars().all()
        total_pending = sum((f.amount for f in pending_fines), Decimal("0.00"))

        return {
            "start_date": start_date.isoformat() if start_date else None,
            "end_date": end_date.isoformat() if end_date else None,
            "total_collected": float(total_collected),
            "total_pending": float(total_pending),
        }

    async def get_report_student_ledger(
        self, session: AsyncSession, student_id: UUID | None = None, start_date: date | None = None, end_date: date | None = None
    ) -> dict:
        query = select(StudentLedger)
        if student_id is not None:
            query = query.where(StudentLedger.student_id == student_id)
        if start_date is not None:
            query = query.where(StudentLedger.transaction_date >= start_date)
        if end_date is not None:
            query = query.where(StudentLedger.transaction_date <= end_date)
        query = query.order_by(StudentLedger.transaction_date.desc())
        entries = (await session.execute(query)).scalars().all()
        return {
            "student_id": str(student_id) if student_id else None,
            "entries": [
                {
                    "id": str(e.id),
                    "student_id": str(e.student_id),
                    "date": e.transaction_date.isoformat() if e.transaction_date else "",
                    "description": e.description,
                    "debit": float(e.debit),
                    "credit": float(e.credit),
                    "balance": float(e.balance),
                    "type": e.transaction_type,
                }
                for e in entries
            ],
        }

    async def get_report_transport_fee(
        self, session: AsyncSession, start_date: date | None = None, end_date: date | None = None
    ) -> dict:
        from app.models.transport_model import StudentTransport
        from app.models.student_model import Student

        students_transport = await session.execute(select(StudentTransport))
        total_students = len(students_transport.scalars().all())
        return {
            "start_date": start_date.isoformat() if start_date else None,
            "end_date": end_date.isoformat() if end_date else None,
            "total_students_on_transport": total_students,
        }

    async def generate_receipt(self, session: AsyncSession, payment_id: UUID) -> dict:
        payment = await payment_repository.get(session, payment_id)
        if payment is None:
            _not_found("Payment not found")
        invoice = await session.get(FeeInvoice, payment.invoice_id)
        student = await session.get(Student, invoice.student_id) if invoice else None
        fee_struct = await session.get(FeeStructure, invoice.fee_type_id) if invoice else None
        school_name = "School ERP"
        return {
            "receipt_number": payment.receipt_number or payment.receipt_no or f"RCPT-{payment.id}",
            "transaction_id": payment.transaction_no,
            "issued_date": payment.payment_date.isoformat() if payment.payment_date else "",
            "student_details": {
                "student_id": str(student.id) if student else "",
                "name": f"{student.first_name or ''} {student.last_name or ''}".strip() if student else "Unknown",
                "class": student.class_name if student else "",
                "admission_no": student.admission_no if student else "",
            },
            "fee_breakdown": [
                {
                    "fee_type": fee_struct.fee_type if fee_struct else "Unknown",
                    "amount": float(invoice.amount) if invoice else 0,
                    "discount": float(invoice.discount_amount) if invoice else 0,
                    "late_fee": float(invoice.late_fee_amount) if invoice else 0,
                    "scholarship": float(invoice.scholarship_amount) if invoice else 0,
                }
            ] if invoice else [],
            "taxes": [],
            "discount": float(invoice.discount_amount) if invoice else 0,
            "payment_mode": payment.payment_method,
            "amount_paid": float(payment.amount_paid),
            "balance_remaining": float(invoice.balance_due) if invoice else 0,
            "school_details": {
                "name": school_name,
                "address": "",
                "contact": "",
            },
        }

    async def generate_invoice(self, session: AsyncSession, invoice_id: UUID) -> dict:
        invoice = await fee_invoice_service.get(session, invoice_id)
        student = await session.get(Student, invoice.student_id)
        fee_struct = await session.get(FeeStructure, invoice.fee_type_id)
        total_paid = await _invoice_total_paid(session, invoice.id)
        net = invoice.net_amount if invoice.net_amount is not None else invoice.amount
        return {
            "invoice_number": invoice.invoice_number or f"INV-{invoice.id}",
            "invoice_date": invoice.invoice_date.isoformat() if invoice.invoice_date else "",
            "due_date": invoice.due_date.isoformat() if invoice.due_date else "",
            "status": invoice.status,
            "student_details": {
                "student_id": str(student.id) if student else "",
                "name": f"{student.first_name or ''} {student.last_name or ''}".strip() if student else "Unknown",
                "class": student.class_name if student else "",
                "admission_no": student.admission_no if student else "",
            },
            "fee_breakdown": [
                {
                    "fee_type": fee_struct.fee_type if fee_struct else "Unknown",
                    "amount": float(invoice.amount),
                    "tax": float(fee_struct.tax_percentage or Decimal("0")),
                }
            ] if fee_struct else [],
            "discount_amount": float(invoice.discount_amount),
            "tax_amount": float(invoice.amount * (fee_struct.tax_percentage or Decimal("0")) / Decimal("100")) if fee_struct else 0,
            "late_fee_amount": float(invoice.late_fee_amount),
            "scholarship_amount": float(invoice.scholarship_amount),
            "total_amount": float(net),
            "paid_amount": float(total_paid),
            "balance_remaining": float(net - total_paid),
        }


finance_service = FinanceService(expense_repository, salary_repository)


student_category_service = CRUDService(
    student_category_repository, "Student category", unique_fields=("category_name",)
)
fee_installment_service = CRUDService(fee_installment_repository, "Fee installment")
student_fee_assignment_service = CRUDService(
    student_fee_assignment_repository, "Student fee assignment"
)
student_ledger_service = CRUDService(student_ledger_repository, "Student ledger")
scholarship_type_service = CRUDService(
    scholarship_type_repository, "Scholarship type", unique_fields=("name",)
)
student_scholarship_service = CRUDService(
    student_scholarship_repository, "Student scholarship"
)
late_fee_rule_service = CRUDService(late_fee_rule_repository, "Late fee rule")
refund_service = CRUDService(refund_request_repository, "Refund request")
expense_category_service = CRUDService(
    expense_category_repository, "Expense category", unique_fields=("name",)
)
other_income_service = CRUDService(other_income_repository, "Other income")
salary_service = CRUDService(salary_repository, "Salary")


async def _invoice_total_paid(session, invoice_id, exclude_payment_id=None):
    query = select(func.coalesce(func.sum(Payment.amount_paid), 0)).where(
        Payment.invoice_id == invoice_id
    )
    if exclude_payment_id is not None:
        query = query.where(Payment.id != exclude_payment_id)
    return (await session.execute(query)).scalar_one()
