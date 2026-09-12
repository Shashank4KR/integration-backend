from app.api.v1.exams.exams import router as exam_router
from app.api.v1.exams.exam_subs import router as exam_sub_router
from app.api.v1.exams.report_cards import router as report_card_router
from app.api.v1.exams.results import router as exam_result_router

__all__ = [
    "exam_router",
    "exam_sub_router",
    "exam_result_router",
    "report_card_router",
]
