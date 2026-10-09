from datetime import date, datetime, timedelta
from decimal import Decimal
import logging
from uuid import UUID

logger = logging.getLogger(__name__)

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.library_model import (
    Book,
    BookCategory,
    BookIssue,
    BookIssueStatus,
    BookReservation,
    FinePayment,
    FinePaymentStatus,
    LibrarySettings,
    ReservationStatus,
)
from app.models.student_model import Student
from app.models.user import User
from app.repositories.library_repository import (
    author_repository,
    book_category_repository,
    book_issue_repository,
    book_repository,
    book_reservation_repository,
    fine_payment_repository,
    library_settings_repository,
    publisher_repository,
)
from app.services.communication_service import notification_service
from app.services.crud_service import CRUDService

FINE_RATE = Decimal("10.00")


def _bad_request(detail: str) -> None:
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)


def _forbidden(detail: str = "Insufficient permissions") -> None:
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=detail)


def _ensure_admin_or_librarian(current_user: User) -> None:
    role_name = current_user.role.role_name if current_user.role is not None else None
    if role_name not in ("ADMIN", "LIBRARIAN"):
        _forbidden("Only admin or librarian users can perform this action")


def _ensure_admin(current_user: User) -> None:
    role_name = current_user.role.role_name if current_user.role is not None else None
    if role_name != "ADMIN":
        _forbidden("Only admin users can perform this action")


class BookCategoryService(CRUDService):
    async def create_category(self, session: AsyncSession, data: dict):
        self._validate_name(data)
        return await self.create(session, data)

    async def update_category(self, session: AsyncSession, item_id: UUID, data: dict):
        self._validate_name(data)
        return await self.update(session, item_id, data)

    async def delete_category(self, session: AsyncSession, item_id: UUID):
        return await self.delete(session, item_id)

    async def get_category(self, session: AsyncSession, item_id: UUID):
        return await self.get(session, item_id)

    async def get_categories(self, session: AsyncSession):
        return await self.list(session)

    async def search(self, session: AsyncSession, query: str):
        return await self.repository.search(session, query)

    def _validate_name(self, data: dict):
        if "category_name" in data and not data["category_name"].strip():
            _bad_request("Category name cannot be empty")


class AuthorService(CRUDService):
    async def create_author(self, session: AsyncSession, data: dict):
        self._validate_name(data)
        return await self.create(session, data)

    async def update_author(self, session: AsyncSession, item_id: UUID, data: dict):
        self._validate_name(data)
        return await self.update(session, item_id, data)

    async def delete_author(self, session: AsyncSession, item_id: UUID):
        return await self.delete(session, item_id)

    async def get_author(self, session: AsyncSession, item_id: UUID):
        return await self.get(session, item_id)

    async def get_authors(self, session: AsyncSession):
        return await self.list(session)

    async def search(self, session: AsyncSession, query: str):
        return await self.repository.search(session, query)

    def _validate_name(self, data: dict):
        if "name" in data and not data["name"].strip():
            _bad_request("Author name cannot be empty")


class PublisherService(CRUDService):
    async def create_publisher(self, session: AsyncSession, data: dict):
        self._validate_name(data)
        return await self.create(session, data)

    async def update_publisher(self, session: AsyncSession, item_id: UUID, data: dict):
        self._validate_name(data)
        return await self.update(session, item_id, data)

    async def delete_publisher(self, session: AsyncSession, item_id: UUID):
        return await self.delete(session, item_id)

    async def get_publisher(self, session: AsyncSession, item_id: UUID):
        return await self.get(session, item_id)

    async def get_publishers(self, session: AsyncSession):
        return await self.list(session)

    async def search(self, session: AsyncSession, query: str):
        return await self.repository.search(session, query)

    def _validate_name(self, data: dict):
        if "name" in data and not data["name"].strip():
            _bad_request("Publisher name cannot be empty")


class BookService(CRUDService):
    async def create_book(self, session: AsyncSession, data: dict):
        await self._validate_book(session, data)
        return await self.create(session, data)

    async def update_book(self, session: AsyncSession, item_id: UUID, data: dict):
        existing = await self.get(session, item_id)
        await self._validate_book(session, data, existing)
        return await self.update(session, item_id, data)

    async def delete_book(self, session: AsyncSession, item_id: UUID):
        item = await self.get(session, item_id)
        item.is_deleted = True
        session.add(item)
        await session.commit()
        await session.refresh(item)
        return item

    async def get_book(self, session: AsyncSession, item_id: UUID):
        return await self.get(session, item_id)

    async def get_books(self, session: AsyncSession):
        return await self.repository.get_all(session)

    async def get_books_by_category(self, session: AsyncSession, category_id: UUID):
        await book_category_service.get_category(session, category_id)
        return await self.repository.get_by_category(session, category_id)

    async def search(self, session: AsyncSession, query: str):
        return await self.repository.search(session, query)

    async def filter_books(
        self, session: AsyncSession, category_id: UUID | None = None,
        status: bool | None = None, language: str | None = None,
    ):
        results = await self.repository.get_all(session)
        if category_id is not None:
            results = [b for b in results if b.category_id == category_id]
        if status is not None:
            results = [b for b in results if b.status == status]
        if language is not None:
            results = [b for b in results if b.language == language]
        return results

    async def list_paginated(
        self, session: AsyncSession, skip: int = 0, limit: int = 50
    ):
        return await self.repository.list_paginated(session, skip, limit)

    async def _validate_book(self, session: AsyncSession, data: dict, existing=None):
        for field, label in (("isbn", "ISBN"), ("title", "Title"), ("author", "Author")):
            if field in data and not data[field].strip():
                _bad_request(f"{label} cannot be empty")
        if "category_id" in data and await book_category_repository.get(session, data["category_id"]) is None:
            _bad_request("Book category must exist")
        if "author_id" in data and data["author_id"] is not None:
            if await author_repository.get(session, data["author_id"]) is None:
                _bad_request("Author must exist")
        if "publisher_id" in data and data["publisher_id"] is not None:
            if await publisher_repository.get(session, data["publisher_id"]) is None:
                _bad_request("Publisher must exist")
        total = data.get("total_copies", getattr(existing, "total_copies", None))
        available = data.get("available_copies", getattr(existing, "available_copies", None))
        if total is not None and total <= 0:
            _bad_request("Total copies must be greater than zero")
        if available is not None and available < 0:
            _bad_request("Available copies cannot be negative")
        if total is not None and available is not None and available > total:
            _bad_request("Available copies cannot exceed total copies")


class BookIssueService(CRUDService):
    async def create_issue(self, session: AsyncSession, data: dict):
        return await self._issue(session, data)

    async def issue_book(self, session: AsyncSession, book_id: UUID, data: dict):
        if data["book_id"] != book_id:
            _bad_request("Book ID must match the requested book")
        return await self._issue(session, data)

    async def _issue(self, session: AsyncSession, data: dict):
        book = await book_service.get_book(session, data["book_id"])
        if await session.get(Student, data["student_id"]) is None:
            _bad_request("Student must exist")
        if book.available_copies <= 0:
            _bad_request("No copies are available for issue")
        if data["due_date"] <= data["issue_date"]:
            _bad_request("Due date must be after issue date")
        if await self.repository.get_active_issue(session, data["book_id"], data["student_id"]):
            _bad_request("Student already has an active issue for this book")
        settings = await library_settings_service.get_settings(session)
        student_issues = await self.repository.get_by_student(session, data["student_id"])
        active_count = len([i for i in student_issues if i.status in (BookIssueStatus.ISSUED.value, BookIssueStatus.OVERDUE.value)])
        if active_count >= settings.max_books_per_student:
            _bad_request(f"Student has reached the maximum of {settings.max_books_per_student} books")
        issue = await self.repository.create(session, {**data, "fine_amount": Decimal("0.00"), "status": BookIssueStatus.ISSUED.value})
        book.available_copies -= 1
        session.add(book)
        await session.commit()
        await session.refresh(issue)

        try:
            student_user_id = await self._get_student_user_id(session, data["student_id"])
            if student_user_id:
                await notification_service.create(session, {
                    "user_id": student_user_id,
                    "title": "Book Issued",
                    "message": f"'{book.title}' has been issued to you. Due date: {data['due_date']}.",
                })
                await session.commit()
        except Exception as e:
            logger.warning(f"Failed to send book issued notification: {e}")
        return issue

    async def update_issue(self, session: AsyncSession, item_id: UUID, data: dict):
        issue = await self.get(session, item_id)
        issue_date = data.get("issue_date", issue.issue_date)
        due_date = data.get("due_date", issue.due_date)
        if due_date <= issue_date:
            _bad_request("Due date must be after issue date")
        return await self.update(session, item_id, data)

    async def return_book(self, session: AsyncSession, item_id: UUID, return_date: date | None):
        issue = await self.get(session, item_id)
        if issue.status == BookIssueStatus.RETURNED.value:
            _bad_request("Book issue has already been returned")
        returned_on = return_date or date.today()
        if returned_on < issue.issue_date:
            _bad_request("Return date cannot be before issue date")
        book = await book_service.get_book(session, issue.book_id)
        issue.return_date = returned_on
        issue.status = BookIssueStatus.RETURNED.value
        issue.fine_amount = self._fine(issue.due_date, returned_on)
        if issue.fine_amount > 0:
            issue.fine_paid = False
        book.available_copies += 1
        session.add_all([issue, book])
        await session.commit()
        await session.refresh(issue)

        try:
            student_user_id = await self._get_student_user_id(session, issue.student_id)
            if student_user_id:
                fine_msg = f" A fine of ₹{issue.fine_amount} was applied." if issue.fine_amount > 0 else ""
                await notification_service.create(session, {
                    "user_id": student_user_id,
                    "title": "Book Returned",
                    "message": f"'{book.title}' has been successfully returned.{fine_msg}",
                })
                await session.commit()
        except Exception as e:
            logger.warning(f"Failed to send book returned notification: {e}")
        return issue

    async def refresh_overdue(self, session: AsyncSession):
        issues = await self.repository.get_overdue(session)
        changed = False
        for issue in issues:
            amount = self._fine(issue.due_date, date.today())
            if issue.status != BookIssueStatus.OVERDUE.value or issue.fine_amount != amount:
                issue.status = BookIssueStatus.OVERDUE.value
                issue.fine_amount = amount
                changed = True
        if changed:
            await session.commit()
        return issues

    async def get_issue(self, session: AsyncSession, item_id: UUID):
        await self.refresh_overdue(session)
        return await self.get(session, item_id)

    async def get_issues(self, session: AsyncSession):
        await self.refresh_overdue(session)
        return await self.list(session)

    async def get_by_student(self, session: AsyncSession, student_id: UUID):
        if await session.get(Student, student_id) is None:
            _bad_request("Student must exist")
        await self.refresh_overdue(session)
        return await self.repository.get_by_student(session, student_id)

    async def get_overdue(self, session: AsyncSession):
        return await self.refresh_overdue(session)

    async def delete_issue(self, session: AsyncSession, item_id: UUID):
        issue = await self.get(session, item_id)
        if issue.status != BookIssueStatus.RETURNED.value:
            book = await book_service.get_book(session, issue.book_id)
            book.available_copies += 1
            session.add(book)
        await self.repository.delete(session, issue)
        await session.commit()

    async def pay_fine(self, session: AsyncSession, issue_id: UUID, amount: Decimal):
        issue = await self.get(session, issue_id)
        if issue.fine_amount <= 0:
            _bad_request("No fine to pay")
        if issue.fine_paid:
            _bad_request("Fine has already been paid")
        if amount <= 0:
            _bad_request("Payment amount must be greater than zero")
        if amount > issue.fine_amount:
            _bad_request("Payment amount exceeds the fine amount")
        payment = await fine_payment_repository.create(session, {
            "issue_id": issue_id,
            "amount": amount,
            "status": FinePaymentStatus.PAID.value,
        })
        if amount == issue.fine_amount:
            issue.fine_paid = True
        session.add(issue)
        await session.commit()
        await session.refresh(payment)

        try:
            student_user_id = await self._get_student_user_id(session, issue.student_id)
            if student_user_id:
                await notification_service.create(session, {
                    "user_id": student_user_id,
                    "title": "Fine Paid",
                    "message": f"A fine of ₹{amount} has been paid for '{issue.book.title if hasattr(issue, 'book') else 'a borrowed book'}'.",
                })
                await session.commit()
        except Exception as e:
            logger.warning(f"Failed to send fine paid notification: {e}")
        return payment

    async def get_dashboard_analytics(self, session: AsyncSession) -> dict:
        await self.refresh_overdue(session)
        total_books = await session.scalar(select(func.coalesce(func.sum(Book.total_copies), 0)))
        available_books = await session.scalar(select(func.coalesce(func.sum(Book.available_copies), 0)))
        issued_books = (total_books or 0) - (available_books or 0)
        overdue_count = await session.scalar(
            select(func.count(BookIssue.id)).where(BookIssue.status == BookIssueStatus.OVERDUE.value)
        )
        reserved_count = await session.scalar(
            select(func.count(BookReservation.id)).where(
                BookReservation.status.in_([ReservationStatus.PENDING.value, ReservationStatus.APPROVED.value])
            )
        )
        total_fine = await session.scalar(
            select(func.coalesce(func.sum(BookIssue.fine_amount), 0))
        )
        fine_collected = await session.scalar(
            select(func.coalesce(func.sum(FinePayment.amount), 0))
            .where(FinePayment.status == FinePaymentStatus.PAID.value)
        )
        active_students = await session.scalar(
            select(func.count(func.distinct(BookIssue.student_id))).where(
                BookIssue.status.in_([BookIssueStatus.ISSUED.value, BookIssueStatus.OVERDUE.value])
            )
        )
        issued_today = await self.repository.get_issued_today(session)
        returned_today = await self.repository.get_returned_today(session)
        active_loans = await self.repository.get_active_loans(session)
        overdue_loans = await self.repository.get_overdue(session)
        pending_reservations = await book_reservation_repository.get_pending(session)

        return {
            "total_books": int(total_books or 0),
            "available_books": int(available_books or 0),
            "issued_books": int(issued_books or 0),
            "overdue_books": overdue_count or 0,
            "reserved_books": reserved_count or 0,
            "total_fine": float(total_fine or 0),
            "fine_collected": float(fine_collected or 0),
            "active_students": active_students or 0,
            "issued_today": len(issued_today),
            "returned_today": len(returned_today),
            "active_loans": len(active_loans),
            "overdue_loans": len(overdue_loans),
            "pending_reservations": len(pending_reservations),
        }

    async def get_student_dashboard(self, session: AsyncSession, student_id: UUID) -> dict:
        if await session.get(Student, student_id) is None:
            _bad_request("Student must exist")
        await self.refresh_overdue(session)
        issues = await self.repository.get_by_student(session, student_id)
        active_books = [i for i in issues if i.status in (BookIssueStatus.ISSUED.value, BookIssueStatus.OVERDUE.value)]
        overdue_books = [i for i in issues if i.status == BookIssueStatus.OVERDUE.value]
        returned_books = [i for i in issues if i.status == BookIssueStatus.RETURNED.value]
        total_fine = sum(float(i.fine_amount or 0) for i in issues if not i.fine_paid)
        reservations = await book_reservation_repository.get_active_for_student(session, student_id)
        return {
            "active_books": len(active_books),
            "overdue_books": len(overdue_books),
            "returned_books": len(returned_books),
            "total_fine": total_fine,
            "active_reservations": len(reservations),
        }

    async def _get_student_user_id(self, session: AsyncSession, student_id: UUID) -> UUID | None:
        student = await session.get(Student, student_id)
        if student:
            return student.user_id
        return None

    @staticmethod
    def _fine(due_date: date, comparison_date: date) -> Decimal:
        return Decimal(max(0, (comparison_date - due_date).days)) * FINE_RATE


class BookReservationService(CRUDService):
    async def create_reservation(self, session: AsyncSession, data: dict):
        book = await book_service.get_book(session, data["book_id"])
        if await session.get(Student, data["student_id"]) is None:
            _bad_request("Student must exist")
        has_active = await self._has_active_reservation(session, data["book_id"], data["student_id"])
        if has_active:
            _bad_request("Student already has an active reservation for this book")
        settings = await library_settings_service.get_settings(session)
        student_reservations = await self.repository.get_active_for_student(session, data["student_id"])
        if len(student_reservations) >= settings.reservation_limit:
            _bad_request(f"Student has reached the reservation limit of {settings.reservation_limit}")
        if data.get("reservation_date") is None:
            data["reservation_date"] = date.today()
        reservation = await self.repository.create(session, {**data, "status": ReservationStatus.PENDING.value})
        await session.commit()
        await session.refresh(reservation)

        try:
            student_user_id = await self._get_student_user_id(session, data["student_id"])
            if student_user_id:
                await notification_service.create(session, {
                    "user_id": student_user_id,
                    "title": "Reservation Submitted",
                    "message": f"Your reservation for '{book.title}' has been submitted and is pending approval.",
                })
                await session.commit()
        except Exception as e:
            logger.warning(f"Failed to send reservation submitted notification: {e}")
        return reservation

    async def _has_active_reservation(self, session: AsyncSession, book_id: UUID, student_id: UUID) -> bool:
        result = await session.execute(
            select(BookReservation).where(
                BookReservation.book_id == book_id,
                BookReservation.student_id == student_id,
                BookReservation.status.in_([ReservationStatus.PENDING.value, ReservationStatus.APPROVED.value]),
            )
        )
        return result.scalar_one_or_none() is not None

    async def approve_reservation(self, session: AsyncSession, reservation_id: UUID, current_user: User):
        _ensure_admin_or_librarian(current_user)
        reservation = await self.get(session, reservation_id)
        if reservation.status != ReservationStatus.PENDING.value:
            _bad_request("Only pending reservations can be approved")
        book = await book_service.get_book(session, reservation.book_id)
        if book.available_copies <= 0:
            _bad_request("No copies are available for this book")
        reservation.status = ReservationStatus.APPROVED.value
        reservation.approval_date = date.today()
        session.add(reservation)
        await session.commit()
        await session.refresh(reservation)

        try:
            student_user_id = await self._get_student_user_id(session, reservation.student_id)
            if student_user_id:
                await notification_service.create(session, {
                    "user_id": student_user_id,
                    "title": "Reservation Approved",
                    "message": f"Your reservation for '{book.title}' has been approved. Please visit the library to collect the book.",
                })
                await session.commit()
        except Exception as e:
            logger.warning(f"Failed to send reservation approved notification: {e}")
        return reservation

    async def reject_reservation(self, session: AsyncSession, reservation_id: UUID, current_user: User):
        _ensure_admin_or_librarian(current_user)
        reservation = await self.get(session, reservation_id)
        if reservation.status != ReservationStatus.PENDING.value:
            _bad_request("Only pending reservations can be rejected")
        reservation.status = ReservationStatus.REJECTED.value
        session.add(reservation)
        await session.commit()
        await session.refresh(reservation)

        try:
            student_user_id = await self._get_student_user_id(session, reservation.student_id)
            if student_user_id:
                book = await book_service.get_book(session, reservation.book_id)
                await notification_service.create(session, {
                    "user_id": student_user_id,
                    "title": "Reservation Rejected",
                    "message": f"Your reservation for '{book.title}' has been rejected. Please contact the librarian for more information.",
                })
                await session.commit()
        except Exception as e:
            logger.warning(f"Failed to send reservation rejected notification: {e}")
        return reservation

    async def cancel_reservation(self, session: AsyncSession, reservation_id: UUID, current_user: User):
        reservation = await self.get(session, reservation_id)
        if current_user.role.role_name == "STUDENT":
            student = await session.get(Student, reservation.student_id)
            if student and student.user_id != current_user.id:
                _forbidden("You can only cancel your own reservations")
        else:
            _ensure_admin_or_librarian(current_user)
        if reservation.status not in (ReservationStatus.PENDING.value, ReservationStatus.APPROVED.value):
            _bad_request("Only pending or approved reservations can be cancelled")
        reservation.status = ReservationStatus.CANCELLED.value
        session.add(reservation)
        await session.commit()
        await session.refresh(reservation)
        return reservation

    async def get_reservation(self, session: AsyncSession, item_id: UUID):
        return await self.get(session, item_id)

    async def get_reservations(self, session: AsyncSession):
        return await self.list(session)

    async def get_pending(self, session: AsyncSession):
        return await self.repository.get_pending(session)

    async def get_by_student(self, session: AsyncSession, student_id: UUID):
        return await self.repository.get_by_student(session, student_id)

    async def _get_student_user_id(self, session: AsyncSession, student_id: UUID) -> UUID | None:
        student = await session.get(Student, student_id)
        if student:
            return student.user_id
        return None


class FinePaymentService(CRUDService):
    async def create_payment(self, session: AsyncSession, data: dict):
        return await self.create(session, data)

    async def get_payment(self, session: AsyncSession, item_id: UUID):
        return await self.get(session, item_id)

    async def get_payments(self, session: AsyncSession):
        return await self.list(session)

    async def get_by_issue(self, session: AsyncSession, issue_id: UUID):
        return await self.repository.get_by_issue(session, issue_id)

    async def get_by_student(self, session: AsyncSession, student_id: UUID):
        return await self.repository.get_by_student(session, student_id)

    async def get_today_collection(self, session: AsyncSession):
        return await self.repository.get_today_collection(session)

    async def get_summary(self, session: AsyncSession) -> dict:
        total_collected = await session.scalar(
            select(func.coalesce(func.sum(FinePayment.amount), 0))
            .where(FinePayment.status == FinePaymentStatus.PAID.value)
        )
        total_outstanding = await session.scalar(
            select(func.coalesce(func.sum(BookIssue.fine_amount), 0))
            .where(BookIssue.fine_amount > 0, BookIssue.fine_paid.is_(False))
        )
        total_waived = await session.scalar(
            select(func.coalesce(func.sum(FinePayment.amount), 0))
            .where(FinePayment.status == FinePaymentStatus.WAIVED.value)
        )
        return {
            "total_collected": float(total_collected or 0),
            "total_outstanding": float(total_outstanding or 0),
            "total_waived": float(total_waived or 0),
        }


class LibrarySettingsService(CRUDService):
    async def get_settings(self, session: AsyncSession):
        settings = await self.repository.get_settings(session)
        if settings is None:
            settings = await self.repository.get_or_create(session)
        return settings

    async def update_settings(self, session: AsyncSession, data: dict):
        settings = await self.get_settings(session)
        return await self.update(session, settings.id, data)

    async def create_settings(self, session: AsyncSession, data: dict):
        existing = await self.repository.get_settings(session)
        if existing is not None:
            _bad_request("Library settings already exist")
        return await self.create(session, data)


class LibraryReportService:
    def __init__(self, book_issue_repo):
        self.book_issue_repo = book_issue_repo

    async def daily_report(self, session: AsyncSession) -> dict:
        today = date.today()
        issues = await self.book_issue_repo.get_issued_today(session)
        returns = await self.book_issue_repo.get_returned_today(session)
        overdue = await self.book_issue_repo.get_overdue(session)
        total_fine = sum(float(i.fine_amount or 0) for i in overdue)
        return {
            "date": today.isoformat(),
            "books_issued": len(issues),
            "books_returned": len(returns),
            "overdue_books": len(overdue),
            "total_fine": total_fine,
        }

    async def weekly_report(self, session: AsyncSession) -> dict:
        week_ago = date.today() - timedelta(days=7)
        result = await session.execute(
            select(BookIssue).where(BookIssue.issue_date >= week_ago)
        )
        issues = list(result.scalars().all())
        result = await session.execute(
            select(BookIssue).where(
                BookIssue.status == BookIssueStatus.RETURNED.value,
                BookIssue.return_date >= week_ago,
            )
        )
        returns = list(result.scalars().all())
        overdue = await self.book_issue_repo.get_overdue(session)
        total_fine = sum(float(i.fine_amount or 0) for i in overdue)
        return {
            "period": f"{week_ago.isoformat()} to {date.today().isoformat()}",
            "books_issued": len(issues),
            "books_returned": len(returns),
            "overdue_books": len(overdue),
            "total_fine": total_fine,
        }

    async def monthly_report(self, session: AsyncSession) -> dict:
        month_start = date.today().replace(day=1)
        result = await session.execute(
            select(BookIssue).where(BookIssue.issue_date >= month_start)
        )
        issues = list(result.scalars().all())
        result = await session.execute(
            select(BookIssue).where(
                BookIssue.status == BookIssueStatus.RETURNED.value,
                BookIssue.return_date >= month_start,
            )
        )
        returns = list(result.scalars().all())
        overdue = await self.book_issue_repo.get_overdue(session)
        total_fine = sum(float(i.fine_amount or 0) for i in overdue)
        return {
            "period": f"{month_start.isoformat()} to {date.today().isoformat()}",
            "books_issued": len(issues),
            "books_returned": len(returns),
            "overdue_books": len(overdue),
            "total_fine": total_fine,
        }

    async def yearly_report(self, session: AsyncSession) -> dict:
        year_start = date.today().replace(month=1, day=1)
        result = await session.execute(
            select(BookIssue).where(BookIssue.issue_date >= year_start)
        )
        issues = list(result.scalars().all())
        result = await session.execute(
            select(BookIssue).where(
                BookIssue.status == BookIssueStatus.RETURNED.value,
                BookIssue.return_date >= year_start,
            )
        )
        returns = list(result.scalars().all())
        overdue = await self.book_issue_repo.get_overdue(session)
        total_fine = sum(float(i.fine_amount or 0) for i in overdue)
        return {
            "period": f"{year_start.isoformat()} to {date.today().isoformat()}",
            "books_issued": len(issues),
            "books_returned": len(returns),
            "overdue_books": len(overdue),
            "total_fine": total_fine,
        }

    async def most_borrowed_books(self, session: AsyncSession, limit: int = 10) -> list:
        result = await session.execute(
            select(Book.title, Book.author, func.count(BookIssue.id).label("times_borrowed"))
            .join(BookIssue, BookIssue.book_id == Book.id)
            .group_by(Book.id)
            .order_by(func.count(BookIssue.id).desc())
            .limit(limit)
        )
        return [
            {"title": row.title, "author": row.author, "times_borrowed": row.times_borrowed}
            for row in result.all()
        ]


book_category_service = BookCategoryService(book_category_repository, "Book category", ("category_name",))
author_service = AuthorService(author_repository, "Author", ("name",))
publisher_service = PublisherService(publisher_repository, "Publisher", ("name",))
book_service = BookService(book_repository, "Book", ("isbn",), foreign_keys={"category_id": BookCategory})
book_issue_service = BookIssueService(book_issue_repository, "Book issue")
book_reservation_service = BookReservationService(book_reservation_repository, "Book reservation")
fine_payment_service = FinePaymentService(fine_payment_repository, "Fine payment")
library_settings_service = LibrarySettingsService(library_settings_repository, "Library settings")
library_report_service = LibraryReportService(book_issue_repository)
