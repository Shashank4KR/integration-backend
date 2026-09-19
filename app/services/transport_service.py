from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.student_model import Student
from app.models.transport_model import Bus, Route, RouteStop, StudentTransport, Driver
from app.repositories.transport_repository import (
    bus_repository,
    driver_repository,
    route_repository,
    student_transport_repository,
)
from app.services.crud_service import CRUDService


def _bad_request(detail: str) -> None:
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)


class BusService(CRUDService):
    async def create_bus(self, session: AsyncSession, data: dict):
        self._validate_bus(data)
        return await self.create(session, data)
    async def update_bus(self, session: AsyncSession, item_id: UUID, data: dict):
        self._validate_bus(data)
        if "capacity" in data:
            assigned = await student_transport_repository.count_by_bus(session, item_id)
            if data["capacity"] < assigned: _bad_request("Capacity cannot be below assigned students")
        return await self.update(session, item_id, data)
    async def delete_bus(self, session: AsyncSession, item_id: UUID): return await self.delete(session, item_id)
    async def get_bus(self, session: AsyncSession, item_id: UUID): return await self.get(session, item_id)
    async def get_buses(self, session: AsyncSession): return await self.list(session)
    def _validate_bus(self, data: dict):
        if "bus_number" in data and not data["bus_number"].strip(): _bad_request("Bus number cannot be empty")
        if "model" in data and not data["model"].strip(): _bad_request("Bus model cannot be empty")
        if "capacity" in data and data["capacity"] <= 0: _bad_request("Capacity must be greater than zero")


class RouteService(CRUDService):
    async def create(self, session: AsyncSession, data: dict):
        stops_data = data.pop("stops", None)
        self._validate_route(data)
        item = await super().create(session, data)
        if stops_data:
            for idx, s in enumerate(stops_data):
                stop_dict = s if isinstance(s, dict) else s.model_dump()
                route_stop = RouteStop(
                    route_id=item.id,
                    stop_name=stop_dict.get("stop_name", "").strip(),
                    stop_order=stop_dict.get("stop_order", idx + 1),
                    pickup_time=stop_dict.get("pickup_time"),
                )
                session.add(route_stop)
            await session.commit()
            await session.refresh(item)
        return item

    async def create_route(self, session: AsyncSession, data: dict):
        return await self.create(session, data)

    async def update(self, session: AsyncSession, item_id: UUID, data: dict):
        stops_data = data.pop("stops", None)
        existing = await self.get(session, item_id)
        self._validate_route(data, existing)
        item = await super().update(session, item_id, data)
        if stops_data is not None:
            from sqlalchemy import delete
            await session.execute(delete(RouteStop).where(RouteStop.route_id == item_id))
            for idx, s in enumerate(stops_data):
                stop_dict = s if isinstance(s, dict) else s.model_dump()
                route_stop = RouteStop(
                    route_id=item.id,
                    stop_name=stop_dict.get("stop_name", "").strip(),
                    stop_order=stop_dict.get("stop_order", idx + 1),
                    pickup_time=stop_dict.get("pickup_time"),
                )
                session.add(route_stop)
            await session.commit()
            await session.refresh(item)
        return item

    async def update_route(self, session: AsyncSession, item_id: UUID, data: dict):
        return await self.update(session, item_id, data)

    async def delete_route(self, session: AsyncSession, item_id: UUID):
        return await self.delete(session, item_id)

    async def get_route(self, session: AsyncSession, item_id: UUID):
        return await self.get(session, item_id)

    async def get_routes(self, session: AsyncSession):
        return await self.list(session)

    def _validate_route(self, data: dict, existing=None):
        for field, label in (("route_name", "Route name"), ("start_point", "Start point"), ("end_point", "End point")):
            if field in data and not data[field].strip(): _bad_request(f"{label} cannot be empty")
        start_point = data.get("start_point", getattr(existing, "start_point", None))
        end_point = data.get("end_point", getattr(existing, "end_point", None))
        if start_point is not None and end_point is not None and start_point.strip().casefold() == end_point.strip().casefold(): _bad_request("Start point cannot equal end point")


class StudentTransportService(CRUDService):
    async def create_transport(self, session: AsyncSession, data: dict):
        await self._validate_transport(session, data)
        return await self.create(session, data)
    async def update_transport(self, session: AsyncSession, item_id: UUID, data: dict):
        existing = await self.get(session, item_id)
        await self._validate_transport(session, data, existing)
        return await self.update(session, item_id, data)
    async def delete_transport(self, session: AsyncSession, item_id: UUID): return await self.delete(session, item_id)
    async def get_transport(self, session: AsyncSession, item_id: UUID): return await self.get(session, item_id)
    async def get_transports(self, session: AsyncSession): return await self.list(session)
    async def get_by_student(self, session: AsyncSession, student_id: UUID):
        if await session.get(Student, student_id) is None: _bad_request("Student must exist")
        allocation = await self.repository.get_by_student(session, student_id)
        if allocation is None: raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student transport allocation not found")
        return allocation
    async def get_by_bus(self, session: AsyncSession, bus_id: UUID):
        await bus_service.get_bus(session, bus_id)
        return await self.repository.get_by_bus(session, bus_id)
    async def get_by_route(self, session: AsyncSession, route_id: UUID):
        await route_service.get_route(session, route_id)
        return await self.repository.get_by_route(session, route_id)

    async def _validate_transport(self, session: AsyncSession, data: dict, existing=None):
        student_id = data.get("student_id", getattr(existing, "student_id", None))
        bus_id = data.get("bus_id", getattr(existing, "bus_id", None))
        route_id = data.get("route_id", getattr(existing, "route_id", None))
        stop_point = data.get("stop_point", getattr(existing, "stop_point", None))
        if not stop_point or not stop_point.strip(): _bad_request("Stop point cannot be empty")
        if await session.get(Student, student_id) is None: _bad_request("Student must exist")
        bus = await bus_service.get_bus(session, bus_id)
        await route_service.get_route(session, route_id)
        allocation = await self.repository.get_by_student(session, student_id)
        if allocation is not None and allocation.id != getattr(existing, "id", None): _bad_request("Student can have only one active transport allocation")
        assigned_students = await self.repository.count_by_bus(session, bus_id, getattr(existing, "id", None))
        if assigned_students >= bus.capacity: _bad_request("Bus is full")


bus_service = BusService(bus_repository, "Bus", ("bus_number",))
route_service = RouteService(route_repository, "Route", ("route_name",))
student_transport_service = StudentTransportService(student_transport_repository, "Student transport")


class DriverService(CRUDService):
    async def get_by_bus(self, session, bus_id):
        return await driver_repository.get_by_bus(session, bus_id)

    async def count_by_bus(self, session, bus_id):
        return await driver_repository.count_by_bus(session, bus_id)


driver_service = DriverService(driver_repository, "Driver", ("license_number",))


async def transport_summary(session: AsyncSession) -> dict:
    total_buses = await session.scalar(select(func.coalesce(func.count(Bus.id), 0)))
    total_routes = await session.scalar(select(func.coalesce(func.count(Route.id), 0)))
    students_using_transport = await session.scalar(select(func.coalesce(func.count(StudentTransport.id), 0)))
    total_drivers = await session.scalar(select(func.coalesce(func.count(Driver.id), 0)))
    assigned_drivers = await session.scalar(select(func.count(Driver.id)).where(Driver.bus_id.isnot(None)))
    total_capacity = await session.scalar(select(func.coalesce(func.sum(Bus.capacity), 0)))
    available_seats = total_capacity - students_using_transport
    return {
        "total_buses": total_buses,
        "total_routes": total_routes,
        "students_using_transport": students_using_transport,
        "total_drivers": total_drivers,
        "assigned_drivers": assigned_drivers,
        "available_seats": available_seats,
        "total_capacity": total_capacity,
    }


async def transport_summary(session: AsyncSession) -> dict:
    total_buses = await session.scalar(select(func.coalesce(func.count(Bus.id), 0)))
    total_routes = await session.scalar(select(func.coalesce(func.count(Route.id), 0)))
    students_using_transport = await session.scalar(select(func.coalesce(func.count(StudentTransport.id), 0)))
    total_drivers = await session.scalar(select(func.coalesce(func.count(Driver.id), 0)))
    assigned_drivers = await session.scalar(select(func.count(Driver.id)).where(Driver.bus_id.isnot(None)))
    total_capacity = await session.scalar(select(func.coalesce(func.sum(Bus.capacity), 0)))
    available_seats = total_capacity - students_using_transport
    return {
        "total_buses": total_buses,
        "total_routes": total_routes,
        "students_using_transport": students_using_transport,
        "total_drivers": total_drivers,
        "assigned_drivers": assigned_drivers,
        "available_seats": available_seats,
        "total_capacity": total_capacity,
    }
