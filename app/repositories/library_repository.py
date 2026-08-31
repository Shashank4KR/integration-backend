from datetime import date
from decimal import Decimal
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.library_model import (
    Author,
    Book,
    BookCategory,
    BookIssue,
    BookIssueStatus,
    BookReservation,
    FinePayment,
    LibrarySettings,
    Publisher,
    ReservationStatus,
)
from app.repositories.crud_repository import CRUDRepository


class BookCategoryRepository(CRUDRepository[BookCategory]):
    async def get_by_id(self, session: AsyncSession, item_id: UUID):
        return await self.get(session, item_id)

    async def get_by_name(self, session: AsyncSession, name: str):
        return (await session.execute(
            select(BookCategory).where(BookCategory.category_name == name)
        )).scalar_one_or_none()

    async def get_all(self, session: AsyncSession):
        return await self.list(session)

    async def search(self, session: AsyncSession, query: str):
        pattern = f"%{query}%"
        result = await session.execute(
            select(BookCategory).where(
                or_(
                    BookCategory.category_name.ilike(pattern),
                    BookCategory.description.ilike(pattern),
                )
            )
        )
        return list(result.scalars().all())


class AuthorRepository(CRUDRepository):
    async def get_by_id(self, session: AsyncSession, item_id: UUID):
        return await self.get(session, item_id)

    async def get_by_name(self, session: AsyncSession, name: str):
        return (await session.execute(
            select(self.model).where(self.model.name == name)
        )).scalar_one_or_none()

    async def get_all(self, session: AsyncSession):
        return await self.list(session)

    async def search(self, session: AsyncSession, query: str):
        pattern = f"%{query}%"
        result = await session.execute(
            select(self.model).where(
                or_(
                    self.model.name.ilike(pattern),
                    self.model.biography.ilike(pattern),
                )
            )
        )
        return list(result.scalars().all())


class PublisherRepository(CRUDRepository):
    async def get_by_id(self, session: AsyncSession, item_id: UUID):
        return await self.get(session, item_id)

    async def get_by_name(self, session: AsyncSession, name: str):
        return (await session.execute(
            select(self.model).where(self.model.name == name)
        )).scalar_one_or_none()

    async def get_all(self, session: AsyncSession):
        return await self.list(session)

    async def search(self, session: AsyncSession, query: str):
        pattern = f"%{query}%"
        result = await session.execute(
            select(self.model).where(
                or_(
                    self.model.name.ilike(pattern),
                    self.model.contact_info.ilike(pattern),
                    self.model.address.ilike(pattern),
                )
            )
        )
        return list(result.scalars().all())


class BookRepository(CRUDRepository[Book]):
    async def get_by_id(self, session: AsyncSession, item_id: UUID):
        result = await session.execute(
            select(Book).where(Book.id == item_id, Book.is_deleted.is_(False))
        )
        return result.scalar_one_or_none()

    async def get_by_isbn(self, session: AsyncSession, isbn: str):
        result = await session.execute(
            select(Book).where(Book.isbn == isbn, Book.is_deleted.is_(False))
        )
        return result.scalar_one_or_none()

    async def get_all(self, session: AsyncSession):
        result = await session.execute(
            select(Book).where(Book.is_deleted.is_(False))
        )
        return list(result.scalars().all())

    async def get_by_category(self, session: AsyncSession, category_id: UUID):
        result = await session.execute(
            select(Book).where(
                Book.category_id == category_id, Book.is_deleted.is_(False)
            )
        )
        return list(result.scalars().all())

    async def search(self, session: AsyncSession, query: str):
        pattern = f"%{query}%"
        result = await session.execute(
            select(Book).where(
                Book.is_deleted.is_(False),
                or_(
                    Book.title.ilike(pattern),
                    Book.author.ilike(pattern),
                    Book.isbn.ilike(pattern),
                    Book.publisher.ilike(pattern),
                ),
            )
        )
        return list(result.scalars().all())

    async def filter_by_category(self, session: AsyncSession, category_id: UUID):
        result = await session.execute(
            select(Book).where(
                Book.category_id == category_id, Book.is_deleted.is_(False)
            )
        )
        return list(result.scalars().all())

    async def filter_by_status(self, session: AsyncSession, status: bool):
        result = await session.execute(
            select(Book).where(
                Book.status == status, Book.is_deleted.is_(False)
            )
        )
        return list(result.scalars().all())

    async def filter_by_language(self, session: AsyncSession, language: str):
        result = await session.execute(
            select(Book).where(
                Book.language == language, Book.is_deleted.is_(False)
            )
        )
        return list(result.scalars().all())

    async def list_paginated(
        self, session: AsyncSession, skip: int = 0, limit: int = 50
    ):
        result = await session.execute(
            select(Book)
            .where(Book.is_deleted.is_(False))
            .offset(skip)
            .limit(limit)
        )
        items = list(result.scalars().all())
        total = await session.scalar(
            select(func.count(Book.id)).where(Book.is_deleted.is_(False))
        )
        return {"items": items, "total": total}


class BookIssueRepository(CRUDRepository[BookIssue]):
    async def get_by_id(self, session: AsyncSession, item_id: UUID):
        return await self.get(session, item_id)

    async def get_all(self, session: AsyncSession):
        return await self.list(session)

    async def get_by_student(self, session: AsyncSession, student_id: UUID):
        result = await session.execute(
            select(BookIssue)
            .where(BookIssue.student_id == student_id)
            .order_by(BookIssue.issue_date.desc())
        )
        return list(result.scalars().all())

    async def get_by_book(self, session: AsyncSession, book_id: UUID):
        result = await session.execute(
            select(BookIssue)
            .where(BookIssue.book_id == book_id)
            .order_by(BookIssue.issue_date.desc())
        )
        return list(result.scalars().all())

    async def get_active_issue(
        self, session: AsyncSession, book_id: UUID, student_id: UUID
    ):
        query = select(BookIssue).where(
            BookIssue.book_id == book_id,
            BookIssue.student_id == student_id,
            BookIssue.status.in_([BookIssueStatus.ISSUED.value, BookIssueStatus.OVERDUE.value]),
        )
        return (await session.execute(query)).scalar_one_or_none()

    async def get_overdue(self, session: AsyncSession):
        query = select(BookIssue).where(
            BookIssue.status != BookIssueStatus.RETURNED.value,
            BookIssue.due_date < date.today(),
        ).order_by(BookIssue.due_date)
        return list((await session.execute(query)).scalars().all())

    async def get_issued_today(self, session: AsyncSession):
        today = date.today()
        result = await session.execute(
            select(BookIssue).where(func.date(BookIssue.issue_date) == today)
        )
        return list(result.scalars().all())

    async def get_returned_today(self, session: AsyncSession):
        today = date.today()
        result = await session.execute(
            select(BookIssue)
            .where(
                BookIssue.status == BookIssueStatus.RETURNED.value,
                func.date(BookIssue.return_date) == today,
            )
        )
        return list(result.scalars().all())

    async def get_active_loans(self, session: AsyncSession):
        result = await session.execute(
            select(BookIssue).where(
                BookIssue.status.in_([BookIssueStatus.ISSUED.value, BookIssueStatus.OVERDUE.value])
            )
        )
        return list(result.scalars().all())

    async def get_by_status(self, session: AsyncSession, status: str):
        result = await session.execute(
            select(BookIssue).where(BookIssue.status == status)
        )
        return list(result.scalars().all())

    async def get_fine_summary(self, session: AsyncSession):
        total_fine = await session.scalar(
            select(func.coalesce(func.sum(BookIssue.fine_amount), 0))
        )
        collected_fine = await session.scalar(
            select(func.coalesce(func.sum(FinePayment.amount), 0))
            .join(FinePayment, FinePayment.issue_id == BookIssue.id)
            .where(FinePayment.status == "PAID")
        )
        outstanding_fine = await session.scalar(
            select(func.coalesce(func.sum(BookIssue.fine_amount), 0))
            .where(BookIssue.fine_amount > 0, BookIssue.fine_paid.is_(False))
        )
        return {
            "total_fine": float(total_fine or 0),
            "collected_fine": float(collected_fine or 0),
            "outstanding_fine": float(outstanding_fine or 0),
        }


class BookReservationRepository(CRUDRepository[BookReservation]):
    async def get_by_id(self, session: AsyncSession, item_id: UUID):
        return await self.get(session, item_id)

    async def get_by_student(self, session: AsyncSession, student_id: UUID):
        result = await session.execute(
            select(BookReservation)
            .where(BookReservation.student_id == student_id)
            .order_by(BookReservation.reservation_date.desc())
        )
        return list(result.scalars().all())

    async def get_by_book(self, session: AsyncSession, book_id: UUID):
        result = await session.execute(
            select(BookReservation)
            .where(BookReservation.book_id == book_id)
            .order_by(BookReservation.reservation_date)
        )
        return list(result.scalars().all())

    async def get_pending(self, session: AsyncSession):
        result = await session.execute(
            select(BookReservation)
            .where(BookReservation.status == ReservationStatus.PENDING.value)
            .order_by(BookReservation.reservation_date)
        )
        return list(result.scalars().all())

    async def get_active_for_student(self, session: AsyncSession, student_id: UUID):
        result = await session.execute(
            select(BookReservation)
            .where(
                BookReservation.student_id == student_id,
                BookReservation.status.in_(
                    [ReservationStatus.PENDING.value, ReservationStatus.APPROVED.value]
                ),
            )
            .order_by(BookReservation.reservation_date.desc())
        )
        return list(result.scalars().all())

    async def count_by_status(self, session: AsyncSession, status: str):
        result = await session.execute(
            select(func.count(BookReservation.id)).where(
                BookReservation.status == status
            )
        )
        return result.scalar_one() or 0


class FinePaymentRepository(CRUDRepository[FinePayment]):
    async def get_by_id(self, session: AsyncSession, item_id: UUID):
        return await self.get(session, item_id)

    async def get_by_issue(self, session: AsyncSession, issue_id: UUID):
        result = await session.execute(
            select(FinePayment).where(FinePayment.issue_id == issue_id)
        )
        return list(result.scalars().all())

    async def get_by_student(self, session: AsyncSession, student_id: UUID):
        result = await session.execute(
            select(FinePayment)
            .join(BookIssue, FinePayment.issue_id == BookIssue.id)
            .where(BookIssue.student_id == student_id)
            .order_by(FinePayment.payment_date.desc())
        )
        return list(result.scalars().all())

    async def get_today_collection(self, session: AsyncSession):
        today = date.today()
        result = await session.execute(
            select(func.coalesce(func.sum(FinePayment.amount), 0))
            .where(
                FinePayment.status == FinePaymentStatus.PAID.value,
                func.date(FinePayment.payment_date) == today,
            )
        )
        return result.scalar_one() or Decimal("0.00")


class LibrarySettingsRepository(CRUDRepository[LibrarySettings]):
    async def get_settings(self, session: AsyncSession):
        result = await session.execute(select(LibrarySettings))
        return result.scalar_one_or_none()

    async def get_or_create(self, session: AsyncSession):
        settings = await self.get_settings(session)
        if settings is None:
            settings = await self.create(session, {
                "max_books_per_student": 5,
                "fine_per_day": Decimal("10.00"),
                "reservation_limit": 3,
                "borrow_duration": 14,
            })
            await session.commit()
            await session.refresh(settings)
        return settings


book_category_repository = BookCategoryRepository(BookCategory)
author_repository = AuthorRepository(Author)
publisher_repository = PublisherRepository(Publisher)
book_repository = BookRepository(Book)
book_issue_repository = BookIssueRepository(BookIssue)
book_reservation_repository = BookReservationRepository(BookReservation)
fine_payment_repository = FinePaymentRepository(FinePayment)
library_settings_repository = LibrarySettingsRepository(LibrarySettings)
