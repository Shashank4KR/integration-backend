import hashlib
import json
from typing import Any
from uuid import UUID

from fastapi import HTTPException, status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.idempotency_model import IdempotencyRecord


class IdempotencyService:
    @staticmethod
    def compute_hash(payload_data: Any) -> str:
        serialized = json.dumps(jsonable_encoder(payload_data), sort_keys=True, default=str)
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

    @staticmethod
    async def get_or_create(
        session: AsyncSession,
        idempotency_key: str | None,
        user_id: UUID,
        endpoint: str,
        payload_data: Any,
    ) -> tuple[IdempotencyRecord | None, JSONResponse | None]:
        """
        Checks for an existing idempotency record.
        Returns:
            (record, None) if a new record was initiated and the caller should process the operation.
            (None, JSONResponse) if an existing completed response is cached and can be returned immediately.
            Raises 409 Conflict if a matching request is currently in-flight.
        """
        if not idempotency_key:
            return None, None

        key = idempotency_key.strip()
        if not key:
            return None, None

        req_hash = IdempotencyService.compute_hash(payload_data)

        # Check existing
        stmt = select(IdempotencyRecord).where(
            IdempotencyRecord.idempotency_key == key,
            IdempotencyRecord.user_id == user_id,
        )
        result = await session.execute(stmt)
        record = result.scalar_one_or_none()

        if record is not None:
            if record.status == "PROCESSING":
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="A request with this Idempotency-Key is currently being processed",
                )
            if record.status == "COMPLETED":
                headers = {
                    "X-Cache": "HIT",
                    "Idempotent-Replayed": "true",
                }
                return None, JSONResponse(
                    status_code=record.response_status or 200,
                    content=record.response_body,
                    headers=headers,
                )

        # Initiate new in-progress record
        new_record = IdempotencyRecord(
            idempotency_key=key,
            user_id=user_id,
            endpoint=endpoint,
            request_hash=req_hash,
            status="PROCESSING",
        )
        session.add(new_record)
        await session.flush()
        return new_record, None

    @staticmethod
    async def complete(
        session: AsyncSession,
        record: IdempotencyRecord | None,
        status_code: int,
        response_body: Any,
    ) -> None:
        if record is None:
            return
        record.status = "COMPLETED"
        record.response_status = status_code
        record.response_body = jsonable_encoder(response_body)
        session.add(record)
        await session.flush()

    @staticmethod
    async def fail(
        session: AsyncSession,
        record: IdempotencyRecord | None,
    ) -> None:
        """Removes an in-progress record so client can safely retry after an error."""
        if record is None:
            return
        await session.delete(record)
        await session.flush()
