from datetime import date
from decimal import Decimal
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.fee_model import FeeInvoice, FeeStructure, Payment
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
from app.repositories.crud_repository import CRUDRepository


class ExpenseRepository(CRUDRepository[Expense]):
    async def get_by_id(self, session: AsyncSession, item_id: UUID):
        return await self.get(session, item_id)

    async def get_all(self, session: AsyncSession):
        return await self.list(session)

    async def get_by_category(self, session: AsyncSession, category: str):
        return list(
            (await session.execute(select(Expense).where(Expense.category == category))).scalars().all()
        )

    async def get_by_date_range(
        self, session: AsyncSession, start_date: date, end_date: date
    ) -> list[Expense]:
        result = await session.execute(
            select(Expense).where(
                Expense.expense_date >= start_date, Expense.expense_date <= end_date
            )
        )
        return list(result.scalars().all())

    async def sum_by_category(self, session: AsyncSession, category: str):
        result = await session.execute(
            select(func.coalesce(func.sum(Expense.amount), 0)).where(Expense.category == category)
        )
        return result.scalar_one()

    async def sum_by_date_range(
        self, session: AsyncSession, start_date: date, end_date: date
    ) -> float:
        result = await session.execute(
            select(func.coalesce(func.sum(Expense.amount), 0)).where(
                Expense.expense_date >= start_date, Expense.expense_date <= end_date
            )
        )
        return float(result.scalar_one())

    async def total(self, session: AsyncSession):
        result = await session.execute(select(func.coalesce(func.sum(Expense.amount), 0)))
        return result.scalar_one()

    async def expenses_by_category(
        self, session: AsyncSession
    ) -> list[dict]:
        query = (
            select(
                Expense.category,
                func.coalesce(func.sum(Expense.amount), 0).label("total"),
            )
            .group_by(Expense.category)
            .order_by(func.coalesce(func.sum(Expense.amount), 0).desc())
        )
        result = await session.execute(query)
        return [{"category": row.category, "total": float(row.total)} for row in result.all()]


class SalaryRepository(CRUDRepository[Salary]):
    async def get_by_id(self, session: AsyncSession, item_id: UUID):
        return await self.get(session, item_id)

    async def get_all(self, session: AsyncSession):
        return await self.list(session)

    async def get_by_month_year(self, session: AsyncSession, month: int, year: int):
        result = await session.execute(
            select(Salary).where(Salary.month == month, Salary.year == year)
        )
        return list(result.scalars().all())

    async def total(self, session: AsyncSession):
        result = await session.execute(select(func.coalesce(func.sum(Salary.amount), 0)))
        return result.scalar_one()

    async def total_by_date_range(
        self, session: AsyncSession, start_date: date, end_date: date
    ) -> float:
        result = await session.execute(
            select(func.coalesce(func.sum(Salary.amount), 0)).where(
                Salary.payment_date >= start_date, Salary.payment_date <= end_date
            )
        )
        return float(result.scalar_one())


class ExpenseCategoryRepository(CRUDRepository[ExpenseCategory]):
    async def get_by_id(self, session: AsyncSession, item_id: UUID):
        return await self.get(session, item_id)

    async def get_all(self, session: AsyncSession):
        return await self.list(session)

    async def get_by_name(self, session: AsyncSession, name: str):
        return await self.get_by_field(session, "name", name)


class StudentCategoryRepository(CRUDRepository[StudentCategory]):
    async def get_by_id(self, session: AsyncSession, item_id: UUID):
        return await self.get(session, item_id)

    async def get_all(self, session: AsyncSession):
        return await self.list(session)

    async def get_active(self, session: AsyncSession) -> list[StudentCategory]:
        result = await session.execute(
            select(StudentCategory).where(StudentCategory.is_active.is_(True))
        )
        return list(result.scalars().all())

    async def get_by_name(self, session: AsyncSession, name: str):
        return await self.get_by_field(session, "category_name", name)


class FeeInstallmentRepository(CRUDRepository[FeeInstallment]):
    async def get_by_id(self, session: AsyncSession, item_id: UUID):
        return await self.get(session, item_id)

    async def get_all(self, session: AsyncSession):
        return await self.list(session)

    async def get_by_fee_structure(
        self, session: AsyncSession, fee_structure_id: UUID
    ) -> list[FeeInstallment]:
        result = await session.execute(
            select(FeeInstallment).where(FeeInstallment.fee_structure_id == fee_structure_id)
        )
        return list(result.scalars().all())

    async def get_by_student_assignment(
        self, session: AsyncSession, assignment_ids: list[UUID]
    ) -> list[FeeInstallment]:
        if not assignment_ids:
            return []
        result = await session.execute(
            select(FeeInstallment)
            .join(FeeStructure)
            .join(StudentFeeAssignment, StudentFeeAssignment.fee_structure_id == FeeStructure.id)
            .where(StudentFeeAssignment.id.in_(assignment_ids))
        )
        return list(result.scalars().all())


fee_installment_repository = FeeInstallmentRepository(FeeInstallment)


class StudentFeeAssignmentRepository(CRUDRepository[StudentFeeAssignment]):
    async def get_by_id(self, session: AsyncSession, item_id: UUID):
        return await self.get(session, item_id)

    async def get_all(self, session: AsyncSession):
        return await self.list(session)

    async def get_by_student(
        self, session: AsyncSession, student_id: UUID
    ) -> list[StudentFeeAssignment]:
        result = await session.execute(
            select(StudentFeeAssignment).where(
                StudentFeeAssignment.student_id == student_id
            )
        )
        return list(result.scalars().all())

    async def get_by_student_and_year(
        self, session: AsyncSession, student_id: UUID, academic_year: str
    ) -> list[StudentFeeAssignment]:
        result = await session.execute(
            select(StudentFeeAssignment)
            .where(
                StudentFeeAssignment.student_id == student_id,
                StudentFeeAssignment.academic_year == academic_year,
            )
        )
        return list(result.scalars().all())

    async def get_unpaid_balance(
        self, session: AsyncSession, student_id: UUID
    ) -> Decimal:
        result = await session.execute(
            select(
                func.coalesce(
                    func.sum(
                        StudentFeeAssignment.net_amount
                        - func.coalesce(
                            (
                                select(func.coalesce(func.sum(Payment.amount_paid), 0))
                                .where(Payment.invoice_id == FeeInvoice.id)
                                .correlate(FeeInvoice)
                                .scalar_subquery()
                            ),
                            0,
                        )
                    ),
                    0,
                )
            ).where(
                StudentFeeAssignment.student_id == student_id,
                StudentFeeAssignment.status == "ACTIVE",
                FeeInvoice.assignment_id == StudentFeeAssignment.id,
                FeeInvoice.status.in_(["UNPAID", "PENDING", "PARTIAL", "OVERDUE"]),
            )
        )
        return result.scalar() or Decimal("0.00")


class StudentLedgerRepository(CRUDRepository[StudentLedger]):
    async def get_by_id(self, session: AsyncSession, item_id: UUID):
        return await self.get(session, item_id)

    async def get_all(self, session: AsyncSession):
        return await self.list(session)

    async def get_by_student(
        self, session: AsyncSession, student_id: UUID
    ) -> list[StudentLedger]:
        result = await session.execute(
            select(StudentLedger)
            .where(StudentLedger.student_id == student_id)
            .order_by(StudentLedger.transaction_date.desc())
        )
        return list(result.scalars().all())

    async def get_by_student_and_type(
        self, session: AsyncSession, student_id: UUID, transaction_type: str
    ) -> list[StudentLedger]:
        result = await session.execute(
            select(StudentLedger)
            .where(
                StudentLedger.student_id == student_id,
                StudentLedger.transaction_type == transaction_type,
            )
            .order_by(StudentLedger.transaction_date.desc())
        )
        return list(result.scalars().all())

    async def get_current_balance(
        self, session: AsyncSession, student_id: UUID
    ) -> Decimal:
        result = await session.execute(
            select(func.coalesce(func.max(StudentLedger.balance), 0)).where(
                StudentLedger.student_id == student_id
            )
        )
        return result.scalar() or Decimal("0.00")

    async def get_ledger_summary(
        self, session: AsyncSession, student_id: UUID
    ) -> dict:
        result = await session.execute(
            select(
                func.coalesce(func.sum(StudentLedger.debit), 0).label("total_debit"),
                func.coalesce(func.sum(StudentLedger.credit), 0).label("total_credit"),
                func.coalesce(func.max(StudentLedger.balance), 0).label("balance"),
            ).where(StudentLedger.student_id == student_id)
        )
        row = result.one()
        return {
            "total_debit": float(row.total_debit),
            "total_credit": float(row.total_credit),
            "balance": float(row.balance),
        }


class ScholarshipTypeRepository(CRUDRepository[ScholarshipType]):
    async def get_by_id(self, session: AsyncSession, item_id: UUID):
        return await self.get(session, item_id)

    async def get_all(self, session: AsyncSession):
        return await self.list(session)

    async def get_active(self, session: AsyncSession) -> list[ScholarshipType]:
        result = await session.execute(
            select(ScholarshipType).where(ScholarshipType.is_active.is_(True))
        )
        return list(result.scalars().all())


class StudentScholarshipRepository(CRUDRepository[StudentScholarship]):
    async def get_by_id(self, session: AsyncSession, item_id: UUID):
        return await self.get(session, item_id)

    async def get_all(self, session: AsyncSession):
        return await self.list(session)

    async def get_by_student(
        self, session: AsyncSession, student_id: UUID
    ) -> list[StudentScholarship]:
        result = await session.execute(
            select(StudentScholarship).where(
                StudentScholarship.student_id == student_id
            )
        )
        return list(result.scalars().all())

    async def get_by_student_and_year(
        self, session: AsyncSession, student_id: UUID, academic_year: str
    ) -> list[StudentScholarship]:
        result = await session.execute(
            select(StudentScholarship)
            .where(
                StudentScholarship.student_id == student_id,
                StudentScholarship.academic_year == academic_year,
                StudentScholarship.status == "APPROVED",
            )
        )
        return list(result.scalars().all())

    async def get_pending(self, session: AsyncSession) -> list[StudentScholarship]:
        result = await session.execute(
            select(StudentScholarship).where(
                StudentScholarship.status == "PENDING"
            )
        )
        return list(result.scalars().all())


class LateFeeRuleRepository(CRUDRepository[LateFeeRule]):
    async def get_by_id(self, session: AsyncSession, item_id: UUID):
        return await self.get(session, item_id)

    async def get_all(self, session: AsyncSession):
        return await self.list(session)

    async def get_active(self, session: AsyncSession) -> list[LateFeeRule]:
        result = await session.execute(
            select(LateFeeRule).where(LateFeeRule.is_active.is_(True))
        )
        return list(result.scalars().all())

    async def get_by_fee_structure(
        self, session: AsyncSession, fee_structure_id: UUID
    ) -> list[LateFeeRule]:
        result = await session.execute(
            select(LateFeeRule)
            .where(
                LateFeeRule.fee_structure_id == fee_structure_id,
                LateFeeRule.is_active.is_(True),
            )
        )
        return list(result.scalars().all())


class RefundRequestRepository(CRUDRepository[RefundRequest]):
    async def get_by_id(self, session: AsyncSession, item_id: UUID):
        return await self.get(session, item_id)

    async def get_all(self, session: AsyncSession):
        return await self.list(session)

    async def get_by_student(
        self, session: AsyncSession, student_id: UUID
    ) -> list[RefundRequest]:
        result = await session.execute(
            select(RefundRequest).where(
                RefundRequest.student_id == student_id
            )
        )
        return list(result.scalars().all())

    async def get_by_status(
        self, session: AsyncSession, status: str
    ) -> list[RefundRequest]:
        result = await session.execute(
            select(RefundRequest).where(RefundRequest.status == status)
        )
        return list(result.scalars().all())


class OtherIncomeRepository(CRUDRepository[OtherIncome]):
    async def get_by_id(self, session: AsyncSession, item_id: UUID):
        return await self.get(session, item_id)

    async def get_all(self, session: AsyncSession):
        return await self.list(session)

    async def get_by_date_range(
        self, session: AsyncSession, start_date: date, end_date: date
    ) -> list[OtherIncome]:
        result = await session.execute(
            select(OtherIncome).where(
                OtherIncome.income_date >= start_date,
                OtherIncome.income_date <= end_date,
            )
        )
        return list(result.scalars().all())

    async def total(self, session: AsyncSession) -> float:
        result = await session.execute(
            select(func.coalesce(func.sum(OtherIncome.amount), 0))
        )
        return float(result.scalar_one())

    async def total_by_date_range(
        self, session: AsyncSession, start_date: date, end_date: date
    ) -> float:
        result = await session.execute(
            select(func.coalesce(func.sum(OtherIncome.amount), 0)).where(
                OtherIncome.income_date >= start_date,
                OtherIncome.income_date <= end_date,
            )
        )
        return float(result.scalar_one())

    async def total_by_category(
        self, session: AsyncSession
    ) -> list[dict]:
        query = (
            select(
                OtherIncome.category,
                func.coalesce(func.sum(OtherIncome.amount), 0).label("total"),
            )
            .group_by(OtherIncome.category)
            .order_by(func.coalesce(func.sum(OtherIncome.amount), 0).desc())
        )
        result = await session.execute(query)
        return [{"category": row.category, "total": float(row.total)} for row in result.all()]


expense_repository = ExpenseRepository(Expense)
salary_repository = SalaryRepository(Salary)
expense_category_repository = ExpenseCategoryRepository(ExpenseCategory)
student_category_repository = StudentCategoryRepository(StudentCategory)
fee_installment_repository = FeeInstallmentRepository(FeeInstallment)
student_fee_assignment_repository = StudentFeeAssignmentRepository(StudentFeeAssignment)
student_ledger_repository = StudentLedgerRepository(StudentLedger)
scholarship_type_repository = ScholarshipTypeRepository(ScholarshipType)
student_scholarship_repository = StudentScholarshipRepository(StudentScholarship)
late_fee_rule_repository = LateFeeRuleRepository(LateFeeRule)
refund_request_repository = RefundRequestRepository(RefundRequest)
other_income_repository = OtherIncomeRepository(OtherIncome)
