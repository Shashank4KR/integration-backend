from __future__ import annotations

from datetime import date, datetime, timedelta
from decimal import Decimal
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.fee_model import (
    FeeInvoice,
    FeeStructure,
    InvoiceStatus,
    Payment,
    PaymentMethod,
    PaymentStatus,
)
from app.models.finance_model import (
    LateFeeRule,
    RefundStatus,
    ScholarshipType,
    StudentFeeAssignment,
    StudentLedger,
    StudentScholarship,
)
from app.models.student_model import Student
from app.models.user import User
from app.repositories.fee_repository import (
    fee_invoice_repository,
    fee_structure_repository,
    payment_repository,
)
from app.repositories.finance_repository import (
    expense_category_repository,
    expense_repository,
    late_fee_rule_repository,
    other_income_repository,
    refund_request_repository,
    salary_repository,
    student_category_repository,
    student_fee_assignment_repository,
    student_ledger_repository,
    student_scholarship_repository,
)
from app.services.crud_service import CRUDService

INVOICE_STATUSES = {"PAID", "UNPAID", "PARTIAL", "OVERDUE", "CANCELLED", "PENDING"}
PAYMENT_METHODS = {"CASH", "CARD", "UPI", "BANK_TRANSFER", "ONLINE", "CHEQUE"}


def _bad_request(detail: str) -> None:
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)


def _not_found(detail: str) -> None:
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


async def _invoice_total_paid(session, invoice_id, exclude_payment_id=None):
    query = select(func.coalesce(func.sum(Payment.amount_paid), 0)).where(
        Payment.invoice_id == invoice_id
    )
    if exclude_payment_id is not None:
        query = query.where(Payment.id != exclude_payment_id)
    return (await session.execute(query)).scalar_one()


class FeeStructureService(CRUDService):
    async def create(self, session: AsyncSession, data: dict):
        await self._validate_fee_structure(session, data)
        return await super().create(session, data)

    async def update(self, session: AsyncSession, item_id: UUID, data: dict):
        await self._validate_fee_structure(session, data)
        return await super().update(session, item_id, data)

    async def get_by_academic_year(self, session: AsyncSession, academic_year: str):
        return await fee_structure_repository.get_by_academic_year(session, academic_year)

    async def _validate_fee_structure(self, session: AsyncSession, data: dict) -> None:
        if data.get("amount") is not None and data["amount"] <= 0:
            _bad_request("amount must be greater than 0")
        if data.get("max_discount_percentage") is not None and data["max_discount_percentage"] < 0:
            _bad_request("max_discount_percentage cannot be negative")
        if data.get("tax_percentage") is not None and data["tax_percentage"] < 0:
            _bad_request("tax_percentage cannot be negative")
        if data.get("class_id") is not None:
            from app.models.class_model import Class

            if await session.get(Class, data["class_id"]) is None:
                _bad_request("Class must exist")
        if data.get("student_category_id") is not None:
            from app.models.finance_model import StudentCategory

            if await session.get(StudentCategory, data["student_category_id"]) is None:
                _bad_request("Student category must exist")


class FeeInvoiceService(CRUDService):
    async def create(self, session: AsyncSession, data: dict):
        await self._validate_invoice(session, data)
        await self._calculate_invoice(session, data)
        item = await super().create(session, data)
        await self._set_invoice_status(session, item)
        await self._create_ledger_entry(session, item, "FEE_INVOICE")
        await session.commit()
        await session.refresh(item)
        return item

    async def update(self, session: AsyncSession, item_id: UUID, data: dict):
        item = await self.get(session, item_id)
        merged = {
            "student_id": item.student_id,
            "fee_type_id": item.fee_type_id,
            "invoice_date": item.invoice_date,
            "due_date": item.due_date,
            "amount": item.amount,
            "discount_amount": item.discount_amount,
            "late_fee_amount": item.late_fee_amount,
            "scholarship_amount": item.scholarship_amount,
            "net_amount": item.net_amount,
            "status": item.status,
        }
        merged.update(data)
        await self._validate_invoice(session, merged)
        await self._calculate_invoice(session, merged)
        updated = await super().update(session, item_id, data)
        await self._set_invoice_status(session, updated)
        await session.refresh(updated)
        return updated

    async def get(self, session: AsyncSession, item_id: UUID):
        item = await super().get(session, item_id)
        await self._set_invoice_status(session, item)
        return item

    async def list(self, session: AsyncSession, status: str | None = None):
        if status:
            normalized = status.strip().upper()
            items = await fee_invoice_repository.get_by_status(session, normalized)
        else:
            items = await super().list(session)
        for item in items:
            await self._set_invoice_status(session, item)
        if status:
            normalized = status.strip().upper()
            items = [
                item for item in items
                if (item.status.upper() if item.status else "") == normalized
            ]
        return items

    async def _validate_invoice(self, session: AsyncSession, data: dict) -> None:
        if (
            data.get("due_date")
            and data.get("invoice_date")
            and data["due_date"] < data["invoice_date"]
        ):
            _bad_request("due_date cannot be before invoice_date")
        if await session.get(Student, data["student_id"]) is None:
            _bad_request("Student must exist")
        if await session.get(FeeStructure, data["fee_type_id"]) is None:
            _bad_request("Fee type must exist")
        if data.get("amount") is not None and data["amount"] <= 0:
            _bad_request("amount must be greater than 0")
        if data.get("status") is not None:
            if isinstance(data["status"], str):
                data["status"] = data["status"].strip().upper()
            if data["status"] not in INVOICE_STATUSES:
                _bad_request("Invalid invoice status")

    async def _calculate_invoice(self, session: AsyncSession, data: dict) -> None:
        if data.get("amount") is None:
            fee_struct = await session.get(FeeStructure, data["fee_type_id"])
            data["amount"] = fee_struct.amount
        discount_amount = data.get("discount_amount") or Decimal("0.00")
        late_fee_amount = data.get("late_fee_amount") or Decimal("0.00")
        scholarship_amount = data.get("scholarship_amount") or Decimal("0.00")
        tax_percentage = Decimal("0")
        fee_struct = await session.get(FeeStructure, data["fee_type_id"])
        if fee_struct and fee_struct.tax_percentage:
            tax_percentage = fee_struct.tax_percentage or Decimal("0")
        tax_amount = data["amount"] * (tax_percentage / Decimal("100"))
        net_amount = (
            data["amount"]
            + tax_amount
            - discount_amount
            - scholarship_amount
            + late_fee_amount
        )
        data["net_amount"] = max(net_amount, Decimal("0.00"))
        if data.get("invoice_number") is None:
            data["invoice_number"] = await fee_invoice_repository.generate_invoice_number(
                session, ""
            )

    async def _set_invoice_status(
        self, session: AsyncSession, invoice: FeeInvoice
    ) -> None:
        total_paid = await _invoice_total_paid(session, invoice.id)
        net = invoice.net_amount if invoice.net_amount is not None else invoice.amount
        if invoice.status == InvoiceStatus.CANCELLED.value:
            return
        if total_paid >= net:
            invoice.status = InvoiceStatus.PAID.value
        elif total_paid > 0:
            invoice.status = InvoiceStatus.PARTIAL.value
        elif date.today() > invoice.due_date:
            invoice.status = InvoiceStatus.OVERDUE.value
        else:
            invoice.status = InvoiceStatus.UNPAID.value
        session.add(invoice)
        await session.commit()
        await session.refresh(invoice)

    async def _create_ledger_entry(
        self, session: AsyncSession, invoice: FeeInvoice, txn_type: str
    ) -> None:
        net = invoice.net_amount if invoice.net_amount is not None else invoice.amount
        student = await session.get(Student, invoice.student_id)
        student_name = (
            f"{student.first_name or ''} {student.last_name or ''}".strip()
            if student
            else "Unknown"
        )
        fee_struct = await session.get(FeeStructure, invoice.fee_type_id)
        fee_type_label = fee_struct.fee_type if fee_struct else "FEE"
        description = f"{fee_type_label} Invoice #{invoice.invoice_number or str(invoice.id)}"
        current_balance = await student_ledger_repository.get_current_balance(
            session, invoice.student_id
        )
        ledger_entry = StudentLedger(
            student_id=invoice.student_id,
            transaction_date=invoice.invoice_date,
            description=description,
            debit=net,
            credit=Decimal("0.00"),
            balance=current_balance + net,
            transaction_type=txn_type,
            reference_id=invoice.id,
            reference_type="FeeInvoice",
        )
        session.add(ledger_entry)
        await session.flush()

    async def get_by_student(self, session: AsyncSession, student_id: UUID):
        if await session.get(Student, student_id) is None:
            _not_found("Student not found")
        items = await self.repository.get_by_student(session, student_id)
        for item in items:
            await self._set_invoice_status(session, item)
        return items

    async def get_by_student_and_status(
        self, session: AsyncSession, student_id: UUID, status: str
    ):
        if await session.get(Student, student_id) is None:
            _not_found("Student not found")
        normalized = status.strip().upper() if status else ""
        items = await fee_invoice_repository.get_by_student_and_status(
            session, student_id, normalized
        )
        for item in items:
            await self._set_invoice_status(session, item)
        return [
            item for item in items
            if (item.status.upper() if item.status else "") == normalized
        ]

    async def get_outstanding_by_student(
        self, session: AsyncSession, student_id: UUID
    ):
        if await session.get(Student, student_id) is None:
            _not_found("Student not found")
        items = await fee_invoice_repository.get_unpaid_invoices(session, student_id)
        for item in items:
            await self._set_invoice_status(session, item)
        return items

    async def get_unpaid_invoices(self, session: AsyncSession, student_id: UUID):
        return await self.get_outstanding_by_student(session, student_id)

    async def get_overdue(self, session: AsyncSession, due_date: date):
        return await fee_invoice_repository.get_overdue(session, due_date)

    async def assign_fee_to_student(
        self, session: AsyncSession, student_id: UUID, data: dict
    ) -> list[FeeInvoice]:
        student = await session.get(Student, student_id)
        if student is None:
            _not_found("Student not found")
        fee_struct = await session.get(FeeStructure, data["fee_structure_id"])
        if fee_struct is None:
            _bad_request("Fee structure must exist")
        academic_year = (
            data.get("academic_year") or fee_struct.academic_year or ""
        )
        assignment_data = {
            "student_id": student_id,
            "fee_structure_id": data["fee_structure_id"],
            "academic_year": academic_year,
            "total_amount": fee_struct.amount,
            "discount_amount": Decimal("0.00"),
            "scholarship_amount": Decimal("0.00"),
            "late_fee_amount": Decimal("0.00"),
            "net_amount": fee_struct.amount,
            "due_date": data.get("due_date") or date.today(),
            "status": "ACTIVE",
            "student_category_id": fee_struct.student_category_id,
        }
        assignment = await student_fee_assignment_repository.create(
            session, assignment_data
        )
        await session.flush()
        await session.refresh(assignment)
        invoice = FeeInvoice(
            student_id=student_id,
            fee_type_id=data["fee_structure_id"],
            invoice_date=data.get("invoice_date", date.today()),
            due_date=data.get("due_date") or date.today(),
            amount=fee_struct.amount,
            discount_amount=Decimal("0.00"),
            late_fee_amount=Decimal("0.00"),
            scholarship_amount=Decimal("0.00"),
            net_amount=fee_struct.amount,
            status=InvoiceStatus.PENDING.value,
            assignment_id=assignment.id,
        )
        session.add(invoice)
        await session.flush()
        await session.refresh(invoice)
        await self._set_invoice_status(session, invoice)
        await self._create_ledger_entry(session, invoice, "FEE_INVOICE")
        await session.commit()
        await session.refresh(invoice)
        return [invoice]

    async def get_student_ledger_summary(
        self, session: AsyncSession, student_id: UUID
    ) -> dict:
        if await session.get(Student, student_id) is None:
            _not_found("Student not found")
        return await student_ledger_repository.get_ledger_summary(session, student_id)

    async def get_student_fee_summary(
        self, session: AsyncSession, student_id: UUID
    ) -> dict:
        if await session.get(Student, student_id) is None:
            _not_found("Student not found")
        invoices = await self.repository.get_by_student(session, student_id)
        total_fees = Decimal("0.00")
        paid = Decimal("0.00")
        for invoice in invoices:
            net = (
                invoice.net_amount
                if invoice.net_amount is not None
                else invoice.amount
            )
            total_fees += net
            total_paid = await _invoice_total_paid(session, invoice.id)
            paid += total_paid
        pending = total_fees - paid
        return {
            "student_id": student_id,
            "total_fees": float(total_fees),
            "paid": float(paid),
            "pending": float(max(pending, Decimal("0.00"))),
        }


class PaymentService(CRUDService):
    async def create(self, session: AsyncSession, data: dict):
        invoice = await self._validate_payment(session, data)
        if data.get("receipt_number") is None:
            data["receipt_number"] = await payment_repository.generate_receipt_number(
                session, data.get("payment_date")
            )
        if data.get("payment_status") is None:
            data["payment_status"] = PaymentStatus.COMPLETED.value
        item = await super().create(session, data)
        await fee_invoice_service._set_invoice_status(session, invoice)
        await self._create_ledger_entry(session, item, "FEE_PAYMENT")
        await session.commit()
        await session.refresh(item)
        return item

    async def update(self, session: AsyncSession, item_id: UUID, data: dict):
        item = await self.get(session, item_id)
        merged = {
            "invoice_id": item.invoice_id,
            "amount_paid": item.amount_paid,
            "payment_method": item.payment_method,
        }
        merged.update(data)
        invoice = await self._validate_payment(
            session, merged, exclude_payment_id=item_id
        )
        updated = await super().update(session, item_id, data)
        await fee_invoice_service._set_invoice_status(session, invoice)
        await session.refresh(updated)
        return updated

    async def delete(self, session: AsyncSession, item_id: UUID):
        item = await self.get(session, item_id)
        invoice = await session.get(FeeInvoice, item.invoice_id)
        await super().delete(session, item_id)
        await fee_invoice_service._set_invoice_status(session, invoice)

    async def _validate_payment(
        self, session: AsyncSession, data: dict, exclude_payment_id=None
    ):
        invoice = await session.get(FeeInvoice, data["invoice_id"])
        if invoice is None:
            _bad_request("Invoice must exist")
        if data["amount_paid"] <= 0:
            _bad_request("amount_paid must be greater than 0")
        if data["payment_method"] not in PAYMENT_METHODS:
            _bad_request("Invalid payment method")
        total_paid = await _invoice_total_paid(
            session, invoice.id, exclude_payment_id
        )
        net = invoice.net_amount if invoice.net_amount is not None else invoice.amount
        if total_paid + data["amount_paid"] > net:
            _bad_request("Total payments cannot exceed invoice net amount")
        return invoice

    async def _create_ledger_entry(
        self, session: AsyncSession, payment: Payment, txn_type: str
    ) -> None:
        invoice = await session.get(FeeInvoice, payment.invoice_id)
        if invoice is None:
            return
        current_balance = await student_ledger_repository.get_current_balance(
            session, invoice.student_id
        )
        receipt_ref = payment.receipt_number or payment.receipt_no or ""
        ledger_entry = StudentLedger(
            student_id=invoice.student_id,
            transaction_date=payment.payment_date,
            description=f"Payment received ({payment.payment_method}) - Receipt #{receipt_ref}",
            debit=Decimal("0.00"),
            credit=payment.amount_paid,
            balance=current_balance - payment.amount_paid,
            transaction_type=txn_type,
            reference_id=payment.id,
            reference_type="Payment",
        )
        session.add(ledger_entry)
        await session.flush()

    async def get_by_invoice(self, session: AsyncSession, invoice_id: UUID):
        if await session.get(FeeInvoice, invoice_id) is None:
            _not_found("Fee invoice not found")
        return await self.repository.get_by_invoice(session, invoice_id)

    async def get_by_student(self, session: AsyncSession, student_id: UUID):
        if await session.get(Student, student_id) is None:
            _not_found("Student not found")
        return await self.repository.get_by_student(session, student_id)

    async def summary(self, session: AsyncSession, student_id: UUID):
        invoices = await fee_invoice_service.get_by_student(session, student_id)
        total_fees = Decimal("0.00")
        paid = Decimal("0.00")
        for invoice in invoices:
            net = (
                invoice.net_amount
                if invoice.net_amount is not None
                else invoice.amount
            )
            total_fees += net
            paid += await _invoice_total_paid(session, invoice.id)
        pending = total_fees - paid
        return {
            "student_id": student_id,
            "total_fees": float(total_fees),
            "paid": float(paid),
            "pending": float(max(pending, Decimal("0.00"))),
        }

    async def get_by_date_range(
        self, session: AsyncSession, start_date: date, end_date: date
    ):
        return await payment_repository.get_by_date_range(session, start_date, end_date)

    async def total_paid(self, session: AsyncSession, start_date: date | None = None, end_date: date | None = None):
        return await payment_repository.total_paid(session, start_date=start_date, end_date=end_date)

    async def get_revenue_by_month(self, session: AsyncSession, year: int):
        return await payment_repository.get_revenue_by_month(session, year)


class StudentScholarshipService(CRUDService):
    async def approve(
        self, session: AsyncSession, item_id: UUID, data: dict
    ):
        item = await self.get(session, item_id)
        sch_type = await session.get(ScholarshipType, item.scholarship_type_id)
        if sch_type is None:
            _not_found("Scholarship type not found")
        approved_amount = data.get("approved_amount")
        if approved_amount is None:
            if sch_type.type == "PERCENTAGE":
                fee_invoices = await fee_invoice_repository.get_by_student(
                    session, item.student_id
                )
                total_fees = sum(
                    (inv.net_amount if inv.net_amount else inv.amount for inv in fee_invoices),
                    Decimal("0.00"),
                )
                approved_amount = total_fees * (sch_type.value / Decimal("100"))
            else:
                approved_amount = sch_type.value
        item.approved_amount = approved_amount
        item.approved_by = data.get("approved_by")
        item.approval_date = data.get("approval_date") or datetime.now()
        item.status = "APPROVED"
        updates = {
            "approved_amount": approved_amount,
            "approved_by": data.get("approved_by"),
            "approval_date": item.approval_date,
            "status": "APPROVED",
        }
        await self.repository.update(session, item, updates)
        await session.commit()
        await session.refresh(item)
        return item

    async def reject(self, session: AsyncSession, item_id: UUID, data: dict):
        item = await self.get(session, item_id)
        item.status = "REJECTED"
        if data.get("reason"):
            item.reason = data["reason"]
        await self.repository.update(session, item, {"status": "REJECTED"})
        await session.commit()
        await session.refresh(item)
        return item

    async def get_by_student(self, session: AsyncSession, student_id: UUID):
        if await session.get(Student, student_id) is None:
            _not_found("Student not found")
        return await student_scholarship_repository.get_by_student(session, student_id)


class LateFeeRuleService(CRUDService):
    async def apply_late_fees(self, session: AsyncSession) -> int:
        rules = await late_fee_rule_repository.get_active(session)
        applied = 0
        for rule in rules:
            if rule.fee_structure_id is not None:
                result = await session.execute(
                    select(FeeInvoice).where(
                        FeeInvoice.fee_type_id == rule.fee_structure_id,
                        FeeInvoice.status.in_(
                            ["UNPAID", "PENDING", "PARTIAL", "OVERDUE"]
                        ),
                    )
                )
                invoices = result.scalars().all()
            else:
                result = await session.execute(
                    select(FeeInvoice).where(
                        FeeInvoice.status.in_(
                            ["UNPAID", "PENDING", "PARTIAL", "OVERDUE"]
                        )
                    )
                )
                invoices = result.scalars().all()
            today = date.today()
            for invoice in invoices:
                due = invoice.due_date
                if due is None:
                    continue
                effective_date = due + timedelta(days=rule.grace_period_days)
                if today < effective_date:
                    continue
                if today < effective_date + timedelta(
                    days=rule.applicable_after_days
                ):
                    continue
                if rule.type == "FIXED":
                    late_fee = rule.value
                elif rule.type == "PERCENTAGE":
                    late_fee = invoice.amount * (
                        rule.value / Decimal("100")
                    )
                else:
                    continue
                invoice.late_fee_amount = (
                    invoice.late_fee_amount or Decimal("0.00")
                ) + late_fee
                invoice.net_amount = (
                    invoice.amount
                    - (invoice.discount_amount or Decimal("0.00"))
                    - (invoice.scholarship_amount or Decimal("0.00"))
                    + invoice.late_fee_amount
                )
                session.add(invoice)
                await fee_invoice_service._set_invoice_status(session, invoice)
                await fee_invoice_service._create_ledger_entry(
                    session, invoice, "LATE_FEE"
                )
                applied += 1
        await session.commit()
        return applied


class RefundService(CRUDService):
    async def approve(self, session: AsyncSession, item_id: UUID, data: dict):
        item = await self.get(session, item_id)
        if item.status != RefundStatus.PENDING.value:
            _bad_request("Only pending refund requests can be approved")
        item.status = RefundStatus.APPROVED.value
        item.approved_by = data.get("approved_by")
        item.approval_date = data.get("approval_date") or datetime.now()
        await self.repository.update(
            session,
            item,
            {
                "status": RefundStatus.APPROVED.value,
                "approved_by": data.get("approved_by"),
                "approval_date": item.approval_date,
            },
        )
        await session.commit()
        await session.refresh(item)
        return item

    async def process_refund(self, session: AsyncSession, item_id: UUID, data: dict):
        item = await self.get(session, item_id)
        if item.status != RefundStatus.APPROVED.value:
            _bad_request("Only approved refund requests can be processed")
        item.status = RefundStatus.PROCESSED.value
        item.processed_date = data.get("processed_date") or datetime.now()
        item.transaction_no = data.get("transaction_no")
        await self.repository.update(
            session,
            item,
            {
                "status": RefundStatus.PROCESSED.value,
                "processed_date": item.processed_date,
                "transaction_no": data.get("transaction_no"),
            },
        )
        invoice = await session.get(FeeInvoice, item.invoice_id)
        if invoice:
            current_balance = (
                await student_ledger_repository.get_current_balance(
                    session, invoice.student_id
                )
            )
            ledger_entry = StudentLedger(
                student_id=invoice.student_id,
                transaction_date=date.today(),
                description=f"Refund processed - {item.reason}",
                debit=Decimal("0.00"),
                credit=item.amount,
                balance=current_balance + item.amount,
                transaction_type="REFUND",
                reference_id=item.id,
                reference_type="RefundRequest",
            )
            session.add(ledger_entry)
            await session.flush()
        await session.commit()
        await session.refresh(item)
        return item

    async def reject(self, session: AsyncSession, item_id: UUID, data: dict):
        item = await self.get(session, item_id)
        item.status = RefundStatus.REJECTED.value
        await self.repository.update(
            session, item, {"status": RefundStatus.REJECTED.value}
        )
        await session.commit()
        await session.refresh(item)
        return item


fee_structure_service = FeeStructureService(
    fee_structure_repository, "Fee structure", unique_fields=("fee_type",)
)
fee_invoice_service = FeeInvoiceService(fee_invoice_repository, "Fee invoice")
payment_service = PaymentService(payment_repository, "Payment")
student_scholarship_service = StudentScholarshipService(
    student_scholarship_repository, "Student scholarship"
)
late_fee_rule_service = CRUDService(late_fee_rule_repository, "Late fee rule")
refund_service = RefundService(refund_request_repository, "Refund request")
