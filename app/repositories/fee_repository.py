from uuid import UUID
from datetime import date

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.fee_model import FeeInvoice, FeeStructure, Payment
from app.repositories.crud_repository import CRUDRepository


class FeeStructureRepository(CRUDRepository[FeeStructure]):
    async def get_by_id(self, session: AsyncSession, item_id: UUID) -> FeeStructure | None:
        return await self.get(session, item_id)

    async def get_all(self, session: AsyncSession) -> list[FeeStructure]:
        return await self.list(session)

    async def get_by_fee_type(self, session: AsyncSession, fee_type: str) -> list[FeeStructure]:
        result = await session.execute(
            select(FeeStructure).where(FeeStructure.fee_type == fee_type)
        )
        return list(result.scalars().all())

    async def get_by_academic_year(
        self, session: AsyncSession, academic_year: str
    ) -> list[FeeStructure]:
        result = await session.execute(
            select(FeeStructure).where(FeeStructure.academic_year == academic_year)
        )
        return list(result.scalars().all())

    async def get_by_class_and_section(
        self, session: AsyncSession, class_id: UUID, section: str | None = None
    ) -> list[FeeStructure]:
        query = select(FeeStructure).where(FeeStructure.class_id == class_id)
        if section is not None:
            query = query.where(FeeStructure.section == section)
        result = await session.execute(query)
        return list(result.scalars().all())

    async def get_active_structures(self, session: AsyncSession) -> list[FeeStructure]:
        result = await session.execute(
            select(FeeStructure).where(FeeStructure.is_active.is_(True))
        )
        return list(result.scalars().all())

    async def get_by_student(
        self,
        session: AsyncSession,
        student_id: UUID,
        class_id: UUID | None = None,
        section: str | None = None,
        category_id: UUID | None = None,
    ) -> list[FeeStructure]:
        from app.models.student_model import Student

        query = select(FeeStructure).where(FeeStructure.is_active.is_(True))
        student = await session.get(Student, student_id)
        if student and student.class_id:
            query = query.where(
                (FeeStructure.class_id == student.class_id)
                | (FeeStructure.class_id.is_(None))
            )
        if class_id is not None:
            query = query.where(FeeStructure.class_id == class_id)
        if section is not None:
            query = query.where(
                (FeeStructure.section == section) | (FeeStructure.section.is_(None))
            )
        if category_id is not None:
            query = query.where(
                (FeeStructure.student_category_id == category_id)
                | (FeeStructure.student_category_id.is_(None))
            )
        result = await session.execute(query)
        return list(result.scalars().all())


class FeeInvoiceRepository(CRUDRepository[FeeInvoice]):
    async def get_by_id(self, session: AsyncSession, item_id: UUID) -> FeeInvoice | None:
        return await self.get(session, item_id)

    async def get_all(self, session: AsyncSession) -> list[FeeInvoice]:
        return await self.list(session)

    async def get_by_student(
        self, session: AsyncSession, student_id: UUID
    ) -> list[FeeInvoice]:
        result = await session.execute(
            select(FeeInvoice).where(FeeInvoice.student_id == student_id)
        )
        return list(result.scalars().all())

    async def get_by_student_and_status(
        self, session: AsyncSession, student_id: UUID, status: str
    ) -> list[FeeInvoice]:
        normalized = status.strip().upper() if status else ""
        result = await session.execute(
            select(FeeInvoice)
            .where(FeeInvoice.student_id == student_id)
            .where(func.upper(FeeInvoice.status) == normalized)
        )
        return list(result.scalars().all())

    async def get_by_status(
        self, session: AsyncSession, status: str
    ) -> list[FeeInvoice]:
        normalized = status.strip().upper() if status else ""
        result = await session.execute(
            select(FeeInvoice).where(func.upper(FeeInvoice.status) == normalized)
        )
        return list(result.scalars().all())

    async def get_unpaid_invoices(
        self, session: AsyncSession, student_id: UUID | None = None
    ) -> list[FeeInvoice]:
        statuses = ["UNPAID", "PENDING", "PARTIAL", "OVERDUE"]
        query = select(FeeInvoice).where(FeeInvoice.status.in_(statuses))
        if student_id is not None:
            query = query.where(FeeInvoice.student_id == student_id)
        result = await session.execute(query)
        return list(result.scalars().all())

    async def get_overdue(
        self, session: AsyncSession, as_of_date: date | None = None
    ) -> list[FeeInvoice]:
        check_date = as_of_date or date.today()
        result = await session.execute(
            select(FeeInvoice)
            .where(FeeInvoice.due_date < check_date)
            .where(FeeInvoice.status.in_(["UNPAID", "PENDING", "PARTIAL"]))
        )
        return list(result.scalars().all())

    async def sum_outstanding(
        self, session: AsyncSession, student_id: UUID | None = None
    ) -> float:
        query = select(func.coalesce(func.sum(FeeInvoice.amount), 0))
        if student_id is not None:
            query = query.where(
                FeeInvoice.student_id == student_id,
                FeeInvoice.status.in_(["UNPAID", "PENDING", "PARTIAL", "OVERDUE"]),
            )
        else:
            query = query.where(
                FeeInvoice.status.in_(["UNPAID", "PENDING", "PARTIAL", "OVERDUE"])
            )
        return float((await session.execute(query)).scalar())

    async def generate_invoice_number(
        self, session: AsyncSession, academic_year: str
    ) -> str:
        year_part = academic_year.replace("/", "-")
        count = (
            await session.scalar(
                select(func.coalesce(func.count(FeeInvoice.id), 0))
            )
        ) or 0
        seq = count + 1
        return f"FINV-{year_part}-{seq:06d}"


class PaymentRepository(CRUDRepository[Payment]):
    async def get_by_id(self, session: AsyncSession, item_id: UUID) -> Payment | None:
        return await self.get(session, item_id)

    async def get_all(self, session: AsyncSession) -> list[Payment]:
        return await self.list(session)

    async def get_by_invoice(
        self, session: AsyncSession, invoice_id: UUID
    ) -> list[Payment]:
        result = await session.execute(
            select(Payment).where(Payment.invoice_id == invoice_id)
        )
        return list(result.scalars().all())

    async def get_by_student(
        self, session: AsyncSession, student_id: UUID
    ) -> list[Payment]:
        query = select(Payment).join(FeeInvoice).where(FeeInvoice.student_id == student_id)
        result = await session.execute(query)
        return list(result.scalars().all())

    async def get_by_date_range(
        self, session: AsyncSession, start_date: date, end_date: date
    ) -> list[Payment]:
        result = await session.execute(
            select(Payment).where(
                Payment.payment_date >= start_date, Payment.payment_date <= end_date
            )
        )
        return list(result.scalars().all())

    async def total_paid(
        self,
        session: AsyncSession,
        start_date: date | None = None,
        end_date: date | None = None,
        payment_method: str | None = None,
    ) -> float:
        query = select(func.coalesce(func.sum(Payment.amount_paid), 0))
        if start_date is not None:
            query = query.where(Payment.payment_date >= start_date)
        if end_date is not None:
            query = query.where(Payment.payment_date <= end_date)
        if payment_method is not None:
            query = query.where(Payment.payment_method == payment_method)
        return float((await session.execute(query)).scalar())

    async def generate_receipt_number(
        self, session: AsyncSession, payment_date: date | None = None
    ) -> str:
        check_date = payment_date or date.today()
        year = check_date.year
        month = check_date.month
        count = (
            await session.scalar(
                select(func.coalesce(func.count(Payment.id), 0))
            )
        ) or 0
        seq = count + 1
        return f"RCPT-{year}{month:02d}-{seq:06d}"

    async def get_revenue_by_month(
        self, session: AsyncSession, year: int
    ) -> list[dict]:
        query = (
            select(
                func.extract("month", Payment.payment_date).label("month"),
                func.coalesce(func.sum(Payment.amount_paid), 0).label("total"),
            )
            .where(func.extract("year", Payment.payment_date) == year)
            .group_by("month")
            .order_by("month")
        )
        result = await session.execute(query)
        return [
            {"month": int(row.month), "total": float(row.total)}
            for row in result.all()
        ]


fee_structure_repository = FeeStructureRepository(FeeStructure)
fee_invoice_repository = FeeInvoiceRepository(FeeInvoice)
payment_repository = PaymentRepository(Payment)
