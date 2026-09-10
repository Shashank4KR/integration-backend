from uuid import UUID

from fastapi import APIRouter, Body, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.auth.routes import get_current_user
from app.core.database import get_db
from app.models.library_model import (
    Book,
    BookIssue,
    BookIssueStatus,
)
from app.models.user import User
from app.schemas.library_schema import (
    AuthorCreate,
    AuthorResponse,
    AuthorUpdate,
    BookCategoryCreate,
    BookCategoryResponse,
    BookCategoryUpdate,
    BookCreate,
    BookIssueCreate,
    BookIssueResponse,
    BookIssueUpdate,
    BookResponse,
    BookReturnRequest,
    BookUpdate,
    BookReservationCreate,
    BookReservationResponse,
    BookReservationUpdate,
    FinePaymentCreate,
    FinePaymentResponse,
    FinePaymentUpdate,
    LibrarySettingsCreate,
    LibrarySettingsResponse,
    LibrarySettingsUpdate,
    PublisherCreate,
    PublisherResponse,
    PublisherUpdate,
)
from app.services.library_service import (
    _ensure_admin_or_librarian,
    _forbidden,
    author_service,
    book_category_service,
    book_issue_service,
    book_reservation_service,
    book_service,
    fine_payment_service,
    library_report_service,
    library_settings_service,
    publisher_service,
)

book_category_router = APIRouter()
book_router = APIRouter()
book_issue_router = APIRouter()
student_library_router = APIRouter()
library_router = APIRouter()
author_router = APIRouter()
publisher_router = APIRouter()
reservation_router = APIRouter()
fine_payment_router = APIRouter()
library_settings_router = APIRouter()
library_report_router = APIRouter()


# ── Book Categories ──────────────────────────────────────────────────────────
@book_category_router.post("", response_model=BookCategoryResponse, status_code=status.HTTP_201_CREATED)
async def create_category(
    payload: BookCategoryCreate,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_admin_or_librarian(current_user)
    return await book_category_service.create_category(session, payload.model_dump())


@book_category_router.get("", response_model=list[BookCategoryResponse])
async def get_categories(session: AsyncSession = Depends(get_db)):
    return await book_category_service.get_categories(session)


@book_category_router.get("/{item_id}", response_model=BookCategoryResponse)
async def get_category(item_id: UUID, session: AsyncSession = Depends(get_db)):
    return await book_category_service.get_category(session, item_id)


@book_category_router.put("/{item_id}", response_model=BookCategoryResponse)
async def update_category(
    item_id: UUID,
    payload: BookCategoryUpdate,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_admin_or_librarian(current_user)
    return await book_category_service.update_category(session, item_id, payload.model_dump(exclude_unset=True))


@book_category_router.delete("/{item_id}", status_code=status.HTTP_200_OK)
async def delete_category(
    item_id: UUID,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_admin_or_librarian(current_user)
    await book_category_service.delete_category(session, item_id)
    return {"message": "Deleted successfully"}


@book_category_router.get("/{category_id}/books", response_model=list[BookResponse])
async def get_category_books(category_id: UUID, session: AsyncSession = Depends(get_db)):
    return await book_service.get_books_by_category(session, category_id)


# ── Authors ──────────────────────────────────────────────────────────────────
@author_router.post("", response_model=AuthorResponse, status_code=status.HTTP_201_CREATED)
async def create_author(
    payload: AuthorCreate,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_admin_or_librarian(current_user)
    return await author_service.create_author(session, payload.model_dump())


@author_router.get("", response_model=list[AuthorResponse])
async def get_authors(session: AsyncSession = Depends(get_db)):
    return await author_service.get_authors(session)


@author_router.get("/{item_id}", response_model=AuthorResponse)
async def get_author(item_id: UUID, session: AsyncSession = Depends(get_db)):
    return await author_service.get_author(session, item_id)


@author_router.put("/{item_id}", response_model=AuthorResponse)
async def update_author(
    item_id: UUID,
    payload: AuthorUpdate,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_admin_or_librarian(current_user)
    return await author_service.update_author(session, item_id, payload.model_dump(exclude_unset=True))


@author_router.delete("/{item_id}", status_code=status.HTTP_200_OK)
async def delete_author(
    item_id: UUID,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_admin_or_librarian(current_user)
    await author_service.delete_author(session, item_id)
    return {"message": "Deleted successfully"}


# ── Publishers ───────────────────────────────────────────────────────────────
@publisher_router.post("", response_model=PublisherResponse, status_code=status.HTTP_201_CREATED)
async def create_publisher(
    payload: PublisherCreate,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_admin_or_librarian(current_user)
    return await publisher_service.create_publisher(session, payload.model_dump())


@publisher_router.get("", response_model=list[PublisherResponse])
async def get_publishers(session: AsyncSession = Depends(get_db)):
    return await publisher_service.get_publishers(session)


@publisher_router.get("/{item_id}", response_model=PublisherResponse)
async def get_publisher(item_id: UUID, session: AsyncSession = Depends(get_db)):
    return await publisher_service.get_publisher(session, item_id)


@publisher_router.put("/{item_id}", response_model=PublisherResponse)
async def update_publisher(
    item_id: UUID,
    payload: PublisherUpdate,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_admin_or_librarian(current_user)
    return await publisher_service.update_publisher(session, item_id, payload.model_dump(exclude_unset=True))


@publisher_router.delete("/{item_id}", status_code=status.HTTP_200_OK)
async def delete_publisher(
    item_id: UUID,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_admin_or_librarian(current_user)
    await publisher_service.delete_publisher(session, item_id)
    return {"message": "Deleted successfully"}


# ── Books ────────────────────────────────────────────────────────────────────
@book_router.post("", response_model=BookResponse, status_code=status.HTTP_201_CREATED)
async def create_book(
    payload: BookCreate,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_admin_or_librarian(current_user)
    return await book_service.create_book(session, payload.model_dump())


@book_router.get("", response_model=list[BookResponse])
async def get_books(
    session: AsyncSession = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    search: str | None = Query(None),
    category_id: UUID | None = Query(None),
    status: bool | None = Query(None),
    language: str | None = Query(None),
):
    if search:
        return await book_service.search(session, search)
    if category_id or status is not None or language:
        return await book_service.filter_books(session, category_id, status, language)
    return (await book_service.list_paginated(session, skip, limit))["items"]


@book_router.get("/{item_id}", response_model=BookResponse)
async def get_book(item_id: UUID, session: AsyncSession = Depends(get_db)):
    return await book_service.get_book(session, item_id)


@book_router.put("/{item_id}", response_model=BookResponse)
async def update_book(
    item_id: UUID,
    payload: BookUpdate,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_admin_or_librarian(current_user)
    return await book_service.update_book(session, item_id, payload.model_dump(exclude_unset=True))


@book_router.delete("/{item_id}", status_code=status.HTTP_200_OK)
async def delete_book(
    item_id: UUID,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_admin_or_librarian(current_user)
    await book_service.delete_book(session, item_id)
    return {"message": "Deleted successfully"}


@book_router.post("/{book_id}/issue", response_model=BookIssueResponse, status_code=status.HTTP_201_CREATED)
async def issue_book(
    book_id: UUID,
    payload: BookIssueCreate,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_admin_or_librarian(current_user)
    return await book_issue_service.issue_book(session, book_id, payload.model_dump())


# ── Book Issues ──────────────────────────────────────────────────────────────
@book_issue_router.post("", response_model=BookIssueResponse, status_code=status.HTTP_201_CREATED)
async def create_issue(
    payload: BookIssueCreate,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_admin_or_librarian(current_user)
    return await book_issue_service.create_issue(session, payload.model_dump())


@book_issue_router.get("", response_model=list[BookIssueResponse])
async def get_issues(
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_admin_or_librarian(current_user)
    return await book_issue_service.get_issues(session)


@book_issue_router.get("/overdue", response_model=list[BookIssueResponse])
async def get_overdue_issues(
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_admin_or_librarian(current_user)
    return await book_issue_service.get_overdue(session)


@book_issue_router.get("/{item_id}", response_model=BookIssueResponse)
async def get_issue(
    item_id: UUID,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_admin_or_librarian(current_user)
    return await book_issue_service.get_issue(session, item_id)


@book_issue_router.put("/{item_id}", response_model=BookIssueResponse)
async def update_issue(
    item_id: UUID,
    payload: BookIssueUpdate,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_admin_or_librarian(current_user)
    return await book_issue_service.update_issue(session, item_id, payload.model_dump(exclude_unset=True))


@book_issue_router.delete("/{item_id}", status_code=status.HTTP_200_OK)
async def delete_issue(
    item_id: UUID,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_admin_or_librarian(current_user)
    await book_issue_service.delete_issue(session, item_id)
    return {"message": "Deleted successfully"}


@book_issue_router.patch("/{issue_id}/return", response_model=BookIssueResponse)
async def return_book(
    issue_id: UUID,
    payload: BookReturnRequest,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_admin_or_librarian(current_user)
    return await book_issue_service.return_book(session, issue_id, payload.return_date)


@book_issue_router.post("/{issue_id}/pay-fine", response_model=FinePaymentResponse, status_code=status.HTTP_201_CREATED)
async def pay_fine(
    issue_id: UUID,
    payload: FinePaymentCreate = Body(default=FinePaymentCreate(issue_id=None, amount=0)),
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_admin_or_librarian(current_user)
    return await book_issue_service.pay_fine(session, issue_id, payload.amount)


# ── Student Library ──────────────────────────────────────────────────────────
@student_library_router.get("/{student_id}/book-issues", response_model=list[BookIssueResponse])
async def get_student_issues(
    student_id: UUID,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role.role_name == "STUDENT":
        from app.models.student_model import Student as StudentModel
        student = await session.get(StudentModel, student_id)
        if student and student.user_id != current_user.id:
            _forbidden("You can only view your own book issues")
    else:
        _ensure_admin_or_librarian(current_user)
    return await book_issue_service.get_by_student(session, student_id)


@student_library_router.get("/{student_id}/reservations", response_model=list[BookReservationResponse])
async def get_student_reservations(
    student_id: UUID,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role.role_name == "STUDENT":
        from app.models.student_model import Student as StudentModel
        student = await session.get(StudentModel, student_id)
        if student and student.user_id != current_user.id:
            _forbidden("You can only view your own reservations")
    else:
        _ensure_admin_or_librarian(current_user)
    return await book_reservation_service.get_by_student(session, student_id)


@student_library_router.get("/{student_id}/fines", response_model=list[FinePaymentResponse])
async def get_student_fines(
    student_id: UUID,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role.role_name == "STUDENT":
        from app.models.student_model import Student as StudentModel
        student = await session.get(StudentModel, student_id)
        if student and student.user_id != current_user.id:
            _forbidden("You can only view your own fines")
    else:
        _ensure_admin_or_librarian(current_user)
    return await fine_payment_service.get_by_student(session, student_id)


@student_library_router.get("/{student_id}/dashboard", response_model=dict)
async def get_student_library_dashboard(
    student_id: UUID,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role.role_name == "STUDENT":
        from app.models.student_model import Student as StudentModel
        student = await session.get(StudentModel, student_id)
        if student and student.user_id != current_user.id:
            _forbidden("You can only view your own library data")
    else:
        _ensure_admin_or_librarian(current_user)
    await book_issue_service.refresh_overdue(session)
    return await book_issue_service.get_student_dashboard(session, student_id)


# ── Library Summary / Analytics ──────────────────────────────────────────────
@library_router.get("/summary")
async def library_summary(session: AsyncSession = Depends(get_db)):
    await book_issue_service.refresh_overdue(session)
    total_books = await session.scalar(select(func.coalesce(func.sum(Book.total_copies), 0)))
    available_books = await session.scalar(select(func.coalesce(func.sum(Book.available_copies), 0)))
    overdue_books = await session.scalar(
        select(func.count(BookIssue.id)).where(BookIssue.status == BookIssueStatus.OVERDUE.value)
    )
    return {
        "total_books": total_books,
        "available_books": available_books,
        "issued_books": total_books - available_books,
        "overdue_books": overdue_books,
    }


@library_router.get("/analytics/dashboard", response_model=dict)
async def library_dashboard_analytics(
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_admin_or_librarian(current_user)
    return await book_issue_service.get_dashboard_analytics(session)


@library_router.get("/analytics/student/{student_id}", response_model=dict)
async def library_student_analytics(
    student_id: UUID,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role.role_name == "STUDENT":
        from app.models.student_model import Student as StudentModel
        student = await session.get(StudentModel, student_id)
        if student and student.user_id != current_user.id:
            _forbidden("You can only view your own analytics")
    else:
        _ensure_admin_or_librarian(current_user)
    await book_issue_service.refresh_overdue(session)
    return await book_issue_service.get_student_dashboard(session, student_id)


# ── Library Settings ─────────────────────────────────────────────────────────
@library_settings_router.get("", response_model=LibrarySettingsResponse)
async def get_settings(session: AsyncSession = Depends(get_db)):
    return await library_settings_service.get_settings(session)


@library_settings_router.post("", response_model=LibrarySettingsResponse, status_code=status.HTTP_201_CREATED)
async def create_settings(
    payload: LibrarySettingsCreate,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_admin(current_user)
    return await library_settings_service.create_settings(session, payload.model_dump())


@library_settings_router.put("", response_model=LibrarySettingsResponse)
async def update_settings(
    payload: LibrarySettingsUpdate,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_admin(current_user)
    return await library_settings_service.update_settings(session, payload.model_dump(exclude_unset=True))


# ── Reservations ─────────────────────────────────────────────────────────────
@reservation_router.post("", response_model=BookReservationResponse, status_code=status.HTTP_201_CREATED)
async def create_reservation(
    payload: BookReservationCreate,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role.role_name == "STUDENT":
        from app.models.student_model import Student as StudentModel
        student = await session.get(StudentModel, payload.student_id)
        if student and student.user_id != current_user.id:
            _forbidden("You can only create reservations for yourself")
    else:
        _ensure_admin_or_librarian(current_user)
    return await book_reservation_service.create_reservation(session, payload.model_dump())


@reservation_router.get("", response_model=list[BookReservationResponse])
async def get_reservations(
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_admin_or_librarian(current_user)
    return await book_reservation_service.get_reservations(session)


@reservation_router.get("/pending", response_model=list[BookReservationResponse])
async def get_pending_reservations(
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_admin_or_librarian(current_user)
    return await book_reservation_service.get_pending(session)


@reservation_router.get("/{item_id}", response_model=BookReservationResponse)
async def get_reservation(
    item_id: UUID,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_admin_or_librarian(current_user)
    return await book_reservation_service.get_reservation(session, item_id)


@reservation_router.patch("/{item_id}/approve", response_model=BookReservationResponse)
async def approve_reservation(
    item_id: UUID,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await book_reservation_service.approve_reservation(session, item_id, current_user)


@reservation_router.patch("/{item_id}/reject", response_model=BookReservationResponse)
async def reject_reservation(
    item_id: UUID,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await book_reservation_service.reject_reservation(session, item_id, current_user)


@reservation_router.patch("/{item_id}/cancel", response_model=BookReservationResponse)
async def cancel_reservation(
    item_id: UUID,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await book_reservation_service.cancel_reservation(session, item_id, current_user)


# ── Fine Payments ────────────────────────────────────────────────────────────
@fine_payment_router.post("", response_model=FinePaymentResponse, status_code=status.HTTP_201_CREATED)
async def create_fine_payment(
    payload: FinePaymentCreate,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_admin_or_librarian(current_user)
    return await fine_payment_service.create_payment(session, payload.model_dump())


@fine_payment_router.get("", response_model=list[FinePaymentResponse])
async def get_fine_payments(
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_admin_or_librarian(current_user)
    return await fine_payment_service.get_payments(session)


@fine_payment_router.get("/summary", response_model=dict)
async def get_fine_summary(
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_admin_or_librarian(current_user)
    return await fine_payment_service.get_summary(session)


@fine_payment_router.get("/{item_id}", response_model=FinePaymentResponse)
async def get_fine_payment(
    item_id: UUID,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_admin_or_librarian(current_user)
    return await fine_payment_service.get_payment(session, item_id)


@fine_payment_router.put("/{item_id}", response_model=FinePaymentResponse)
async def update_fine_payment(
    item_id: UUID,
    payload: FinePaymentUpdate,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_admin_or_librarian(current_user)
    return await fine_payment_service.update(session, item_id, payload.model_dump(exclude_unset=True))


@fine_payment_router.delete("/{item_id}", status_code=status.HTTP_200_OK)
async def delete_fine_payment(
    item_id: UUID,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_admin(current_user)
    await fine_payment_service.delete(session, item_id)
    return {"message": "Deleted successfully"}


# ── Reports ──────────────────────────────────────────────────────────────────
@library_report_router.get("/daily", response_model=dict)
async def daily_report(
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_admin_or_librarian(current_user)
    return await library_report_service.daily_report(session)


@library_report_router.get("/weekly", response_model=dict)
async def weekly_report(
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_admin_or_librarian(current_user)
    return await library_report_service.weekly_report(session)


@library_report_router.get("/monthly", response_model=dict)
async def monthly_report(
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_admin_or_librarian(current_user)
    return await library_report_service.monthly_report(session)


@library_report_router.get("/yearly", response_model=dict)
async def yearly_report(
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_admin_or_librarian(current_user)
    return await library_report_service.yearly_report(session)


@library_report_router.get("/most-borrowed", response_model=list)
async def most_borrowed_books(
    session: AsyncSession = Depends(get_db),
    limit: int = Query(10, ge=1, le=50),
    current_user: User = Depends(get_current_user),
):
    _ensure_admin_or_librarian(current_user)
    return await library_report_service.most_borrowed_books(session, limit)