from typing import Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.settings_model import SystemSetting


class SettingsRepository:
    async def get_all(self, session: AsyncSession) -> list[SystemSetting]:
        result = await session.execute(select(SystemSetting))
        return list(result.scalars().all())

    async def get_by_category(self, session: AsyncSession, category: str) -> SystemSetting | None:
        result = await session.execute(
            select(SystemSetting).where(SystemSetting.category == category)
        )
        return result.scalar_one_or_none()

    async def upsert_category(
        self, session: AsyncSession, category: str, config: dict[str, Any]
    ) -> SystemSetting:
        setting = await self.get_by_category(session, category)
        if setting is None:
            setting = SystemSetting(category=category, config=config)
            session.add(setting)
        else:
            # Merge existing and new configs
            merged_config = dict(setting.config or {})
            merged_config.update(config)
            setting.config = merged_config
            session.add(setting)

        await session.commit()
        await session.refresh(setting)
        return setting


settings_repository = SettingsRepository()
