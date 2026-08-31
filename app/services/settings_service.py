from typing import Any
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.settings_model import SystemSetting
from app.repositories.settings_repository import settings_repository


DEFAULT_SETTINGS: dict[str, dict[str, Any]] = {
    "organization": {
        "school_name": "Cognora Global Academy",
        "school_code": "CGA-2026",
        "registered_address": "14 Education Lane, Bengaluru, Karnataka 560001",
        "contact_email": "admin@example.com",
        "contact_phone": "9876543210",
        "website": "https://cognora.academy",
        "academic_year": "2026-2027",
        "affiliation": "Central Board of Secondary Education (CBSE)",
        "logo_url": None,
    },
    "academics": {
        "allow_lesson_plan_edits": True,
        "show_subject_codes": True,
        "max_periods_per_day": 8,
        "period_duration_minutes": 45,
        "passing_grade": "D",
    },
    "attendance": {
        "allow_late_marking": True,
        "notify_absent_parents": True,
        "cutoff_time": "09:30 AM",
        "half_day_threshold_hours": 3.5,
    },
    "examination": {
        "publish_after_approval": True,
        "round_marks_to_decimals": True,
        "min_passing_percentage": 40,
        "grading_scale": "Standard (A+, A, B, C, D, F)",
    },
    "library": {
        "send_overdue_reminders": True,
        "allow_book_reservations": True,
        "max_books_per_student": 3,
        "issue_duration_days": 14,
        "fine_per_day": 5,
    },
    "hostel": {
        "require_visitor_approval": True,
        "enable_late_return_tracking": True,
        "curfew_time": "08:30 PM",
        "late_fine_amount": 50,
    },
    "transport": {
        "share_bus_arrival_alerts": True,
        "require_trip_checkin": True,
        "speed_limit_alerts": True,
        "gps_tracking_enabled": True,
    },
    "finance": {
        "generate_receipts_automatically": True,
        "allow_partial_payments": True,
        "currency": "INR",
        "tax_percentage": 0,
        "late_fee_grace_days": 7,
    },
    "communication": {
        "email_delivery": True,
        "sms_delivery": False,
        "whatsapp_notifications": True,
        "template_approval_workflow": True,
    },
    "roles": {
        "allow_custom_roles": False,
        "session_concurrency_limit": 3,
    },
    "reports": {
        "add_logo_to_exports": True,
        "require_permission_for_csv": True,
        "default_export_format": "PDF",
    },
    "integrations": {
        "payment_gateway": "Razorpay",
        "payment_gateway_connected": True,
        "sms_provider_connected": True,
        "smtp_email_connected": True,
    },
    "system": {
        "maintenance_mode": False,
        "automatic_nightly_backups": True,
        "session_timeout_minutes": 60,
        "max_upload_size_mb": 10,
    },
    "appearance": {
        "theme": "System",
        "language": "English (India)",
        "date_format": "DD MMM YYYY",
        "timezone": "Asia/Kolkata (IST)",
    },
    "notifications": {
        "role_updates": True,
        "email_notifications": True,
        "in_app_notifications": True,
        "sms_notifications": False,
    },
    "security": {
        "two_factor_auth": False,
        "signin_alerts": True,
    },
}


class SettingsService:
    async def get_all_settings(self, session: AsyncSession) -> dict[str, dict[str, Any]]:
        db_settings = await settings_repository.get_all(session)
        result = {k: dict(v) for k, v in DEFAULT_SETTINGS.items()}
        for item in db_settings:
            if item.category in result:
                result[item.category].update(item.config or {})
            else:
                result[item.category] = item.config or {}
        return result

    async def get_category_settings(
        self, session: AsyncSession, category: str
    ) -> dict[str, Any]:
        default = dict(DEFAULT_SETTINGS.get(category, {}))
        item = await settings_repository.get_by_category(session, category)
        if item and item.config:
            default.update(item.config)
        return default

    async def update_category_settings(
        self, session: AsyncSession, category: str, config: dict[str, Any]
    ) -> SystemSetting:
        return await settings_repository.upsert_category(session, category, config)

    async def bulk_update_settings(
        self, session: AsyncSession, settings_dict: dict[str, dict[str, Any]]
    ) -> dict[str, dict[str, Any]]:
        for category, config in settings_dict.items():
            if isinstance(config, dict):
                await settings_repository.upsert_category(session, category, config)
        return await self.get_all_settings(session)


settings_service = SettingsService()
