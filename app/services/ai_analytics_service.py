from datetime import UTC, datetime, timezone
from decimal import ROUND_HALF_UP, Decimal
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.assignment_model import AssignmentSubmission
from app.models.attendance_model import Attendance, AttendanceStatus
from app.models.exam_model import Exam
from app.models.exam_result_model import ExamResult
from app.models.student_model import Student
from app.models.user import User
from app.repositories.ai_analytics_repository import ai_analytics_repository, ai_chat_history_repository

ZERO = Decimal("0")
ONE_HUNDRED = Decimal("100")


class AIAnalyticsService:
    async def generate_student_analytics(self, session: AsyncSession, student_id: UUID):
        await self._get_student(session, student_id)
        attendance_percentage = await self._attendance_percentage(session, student_id)
        performance_percentage = await self._performance_percentage(session, student_id)
        attendance_risk = self._risk(attendance_percentage)
        performance_risk = self._risk(performance_percentage)
        pattern, recommendation = self._insights(attendance_percentage, performance_percentage)
        item = await ai_analytics_repository.create(session, {
            "student_id": student_id,
            "attendance_risk": attendance_risk,
            "performance_risk": performance_risk,
            "predicted_grade": self._grade(performance_percentage),
            "learning_pattern": pattern,
            "recommendation": recommendation,
            "generated_on": datetime.now(UTC),
        })
        await session.commit()
        return item

    async def generate_all_student_analytics(self, session: AsyncSession):
        students = list((await session.execute(select(Student))).scalars().all())
        generated = []
        for student in students:
            attendance_percentage = await self._attendance_percentage(session, student.id)
            performance_percentage = await self._performance_percentage(session, student.id)
            pattern, recommendation = self._insights(attendance_percentage, performance_percentage)
            generated.append(await ai_analytics_repository.create(session, {
                "student_id": student.id,
                "attendance_risk": self._risk(attendance_percentage),
                "performance_risk": self._risk(performance_percentage),
                "predicted_grade": self._grade(performance_percentage),
                "learning_pattern": pattern,
                "recommendation": recommendation,
                "generated_on": datetime.now(UTC),
            }))
        await session.commit()
        return generated

    async def get_student_analytics(self, session: AsyncSession, student_id: UUID):
        await self._get_student(session, student_id)
        return await ai_analytics_repository.get_by_student(session, student_id)

    async def get_analytics(self, session: AsyncSession, analytics_id: UUID):
        item = await ai_analytics_repository.get_by_id(session, analytics_id)
        if item is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="AI analytics not found")
        return item

    async def get_all_analytics(self, session: AsyncSession):
        return await ai_analytics_repository.get_all(session)

    async def delete_analytics(self, session: AsyncSession, analytics_id: UUID):
        item = await self.get_analytics(session, analytics_id)
        await ai_analytics_repository.delete(session, item)
        await session.commit()

    async def high_risk_students(self, session: AsyncSession):
        latest = self._latest_by_student(await self.get_all_analytics(session))
        return [
            {"student_id": item.student_id, "attendance_risk": item.attendance_risk, "performance_risk": item.performance_risk}
            for item in latest.values() if self._risk_level(item) == "high"
        ]

    async def dashboard(self, session: AsyncSession):
        students = list((await session.execute(select(Student.id))).scalars().all())
        latest = self._latest_by_student(await self.get_all_analytics(session))
        counts = {"high": 0, "medium": 0, "low": 0}
        for student_id in students:
            item = latest.get(student_id)
            # Students without a generated report are conservatively high risk.
            counts[self._risk_level(item) if item else "high"] += 1
        return {"total_students": len(students), "high_risk_students": counts["high"], "medium_risk_students": counts["medium"], "low_risk_students": counts["low"]}

    async def _get_student(self, session: AsyncSession, student_id: UUID):
        student = await session.get(Student, student_id)
        if student is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Student must exist")
        return student

    async def _attendance_percentage(self, session: AsyncSession, student_id: UUID) -> Decimal:
        records = list((await session.execute(select(Attendance.status).where(Attendance.student_id == student_id))).scalars().all())
        if not records:
            return ZERO
        attended = sum(record in (AttendanceStatus.PRESENT, AttendanceStatus.LATE, "PRESENT", "LATE") for record in records)
        return self._percentage(Decimal(attended), Decimal(len(records)))

    async def _performance_percentage(self, session: AsyncSession, student_id: UUID) -> Decimal:
        exam_rows = (await session.execute(
            select(ExamResult.marks_obtained, Exam.max_marks).join(Exam, Exam.id == ExamResult.exam_id).where(ExamResult.student_id == student_id)
        )).all()
        percentages = [self._percentage(Decimal(marks), Decimal(max_marks)) for marks, max_marks in exam_rows if max_marks]
        assignment_marks = list((await session.execute(
            select(AssignmentSubmission.marks).where(AssignmentSubmission.student_id == student_id, AssignmentSubmission.marks.is_not(None))
        )).scalars().all())
        percentages.extend(min(ONE_HUNDRED, max(ZERO, Decimal(mark))) for mark in assignment_marks)
        if not percentages:
            return ZERO
        return (sum(percentages, ZERO) / Decimal(len(percentages))).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    @staticmethod
    def _percentage(value: Decimal, maximum: Decimal) -> Decimal:
        return ZERO if maximum <= 0 else min(ONE_HUNDRED, max(ZERO, (value * ONE_HUNDRED / maximum).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)))

    @staticmethod
    def _risk(percentage: Decimal) -> Decimal:
        return (ONE_HUNDRED - percentage).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    @staticmethod
    def _grade(percentage: Decimal) -> str:
        for threshold, grade in ((90, "A+"), (80, "A"), (70, "B"), (60, "C"), (50, "D")):
            if percentage >= threshold:
                return grade
        return "F"

    @staticmethod
    def _insights(attendance: Decimal, performance: Decimal) -> tuple[str, str]:
        patterns, recommendations = [], []
        if performance >= 85: patterns.append("Strong academic performance")
        elif performance < 60: patterns.append("Needs additional support"); recommendations.append("Attend remedial classes")
        else: patterns.append("Developing academic performance")
        if attendance < 75: patterns.append("Attendance needs improvement"); recommendations.append("Improve attendance")
        elif attendance > 85: patterns.append("Excellent consistency")
        if performance < 70: recommendations.append("Increase assignment participation")
        if not recommendations: recommendations.append("Maintain current performance")
        return ". ".join(patterns), ". ".join(dict.fromkeys(recommendations))

    @staticmethod
    def _latest_by_student(items):
        latest = {}
        for item in items:
            if item.student_id not in latest or item.generated_on > latest[item.student_id].generated_on:
                latest[item.student_id] = item
        return latest

    @staticmethod
    def _risk_level(item) -> str:
        score = max(item.attendance_risk, item.performance_risk)
        return "high" if score > 25 else "medium" if score >= 15 else "low"


class AIChatHistoryService:
    async def save_chat(self, session: AsyncSession, data: dict):
        if await session.get(User, data["user_id"]) is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User must exist")
        if not data["question"].strip() or not data["response"].strip():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Question and response cannot be empty")
        if data.get("timestamp") is None:
            data["timestamp"] = datetime.now(UTC)
        item = await ai_chat_history_repository.create(session, data)
        await session.commit()
        return item

    async def get_chat_history(self, session: AsyncSession, chat_id: UUID):
        item = await ai_chat_history_repository.get_by_id(session, chat_id)
        if item is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="AI chat history not found")
        return item

    async def get_all_chat_history(self, session: AsyncSession): return await ai_chat_history_repository.get_all(session)
    async def get_user_chat_history(self, session: AsyncSession, user_id: UUID):
        if await session.get(User, user_id) is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User must exist")
        return await ai_chat_history_repository.get_by_user(session, user_id)
    async def delete_chat(self, session: AsyncSession, chat_id: UUID):
        item = await self.get_chat_history(session, chat_id)
        await ai_chat_history_repository.delete(session, item)
        await session.commit()


ai_analytics_service = AIAnalyticsService()
ai_chat_history_service = AIChatHistoryService()
