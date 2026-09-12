from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.core.database import get_db
from app.core.exceptions import APIException, success_response
from app.api.v1.auth.routes import get_current_user
from app.models.transport_model import Bus, Driver, Route, StudentTransport
from app.models.user import User
from app.schemas.transport_schema import (
    BusCreate, BusResponse, BusUpdate, DriverCreate, DriverResponse, DriverUpdate,
    RouteCreate, RouteResponse, RouteUpdate, StudentTransportCreate, StudentTransportResponse, StudentTransportUpdate,
)
from app.services.transport_service import (
    bus_service, driver_service, route_service, student_transport_service,
    transport_summary,
)


def _ensure_admin(current_user: User) -> None:
    if current_user.role.role_name != "ADMIN":
        raise APIException(
            status_code=status.HTTP_403_FORBIDDEN,
            message="Only admin users can perform this action",
        )


bus_router = APIRouter()


@bus_router.post("", status_code=status.HTTP_201_CREATED)
async def create_bus(payload: BusCreate, session: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    _ensure_admin(current_user)
    return await bus_service.create(session, payload.model_dump())

@bus_router.get("")
async def get_buses(session: AsyncSession = Depends(get_db)): return await bus_service.list(session)

@bus_router.get("/{item_id}")
async def get_bus(item_id: UUID, session: AsyncSession = Depends(get_db)): return await bus_service.get(session, item_id)

@bus_router.put("/{item_id}")
async def update_bus(item_id: UUID, payload: BusUpdate, session: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    _ensure_admin(current_user)
    return await bus_service.update(session, item_id, payload.model_dump(exclude_unset=True))

@bus_router.delete("/{item_id}")
async def delete_bus(item_id: UUID, session: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    _ensure_admin(current_user)
    await bus_service.delete(session, item_id)
    return {"message": "Deleted successfully"}

@bus_router.get("/{bus_id}/students")
async def get_bus_students(bus_id: UUID, session: AsyncSession = Depends(get_db)): return await student_transport_service.get_by_bus(session, bus_id)

@bus_router.get("/{bus_id}/capacity")
async def get_bus_capacity(bus_id: UUID, session: AsyncSession = Depends(get_db)):
    bus = await bus_service.get_bus(session, bus_id)
    assigned_students = await student_transport_service.repository.count_by_bus(session, bus_id)
    return {"bus_id": str(bus.id), "capacity": bus.capacity, "assigned_students": assigned_students, "available_seats": bus.capacity - assigned_students}


route_router = APIRouter()


@route_router.post("", status_code=status.HTTP_201_CREATED)
async def create_route(payload: RouteCreate, session: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    _ensure_admin(current_user)
    return await route_service.create(session, payload.model_dump())

@route_router.get("")
async def get_routes(session: AsyncSession = Depends(get_db)): return await route_service.list(session)

@route_router.get("/{item_id}")
async def get_route(item_id: UUID, session: AsyncSession = Depends(get_db)): return await route_service.get(session, item_id)

@route_router.put("/{item_id}")
async def update_route(item_id: UUID, payload: RouteUpdate, session: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    _ensure_admin(current_user)
    return await route_service.update(session, item_id, payload.model_dump(exclude_unset=True))

@route_router.delete("/{item_id}")
async def delete_route(item_id: UUID, session: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    _ensure_admin(current_user)
    await route_service.delete(session, item_id)
    return {"message": "Deleted successfully"}

@route_router.get("/{route_id}/students")
async def get_route_students(route_id: UUID, session: AsyncSession = Depends(get_db)): return await student_transport_service.get_by_route(session, route_id)


student_transport_router = APIRouter()


@student_transport_router.post("", status_code=status.HTTP_201_CREATED)
async def create_transport(payload: StudentTransportCreate, session: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    _ensure_admin(current_user)
    return await student_transport_service.create(session, payload.model_dump())

@student_transport_router.get("")
async def get_transports(session: AsyncSession = Depends(get_db)): return await student_transport_service.list(session)

@student_transport_router.get("/{item_id}")
async def get_transport(item_id: UUID, session: AsyncSession = Depends(get_db)): return await student_transport_service.get(session, item_id)

@student_transport_router.put("/{item_id}")
async def update_transport(item_id: UUID, payload: StudentTransportUpdate, session: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    _ensure_admin(current_user)
    return await student_transport_service.update(session, item_id, payload.model_dump(exclude_unset=True))

@student_transport_router.delete("/{item_id}")
async def delete_transport(item_id: UUID, session: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    _ensure_admin(current_user)
    await student_transport_service.delete(session, item_id)
    return {"message": "Deleted successfully"}


student_transport_detail_router = APIRouter()
@student_transport_detail_router.get("/{student_id}/transport")
async def get_student_transport(student_id: UUID, session: AsyncSession = Depends(get_db)): return await student_transport_service.get_by_student(session, student_id)


transport_router = APIRouter()


@transport_router.get("/summary")
async def transport_summary_endpoint(session: AsyncSession = Depends(get_db)):
    data = await transport_summary(session)
    return success_response(data)


@transport_router.get("/overview")
async def transport_overview(session: AsyncSession = Depends(get_db)):
    data = await transport_summary(session)

    route_distribution = []
    routes = await route_service.list(session)
    for route in routes:
        student_count = await session.scalar(
            select(func.count(StudentTransport.id)).where(StudentTransport.route_id == route.id)
        )
        route_distribution.append({
            "route_name": route.route_name,
            "start_point": route.start_point,
            "end_point": route.end_point,
            "students": student_count or 0,
            "active": True,
        })

    buses = await bus_service.list(session)
    running_buses = len(buses)
    delayed_buses = 0
    completed_buses = 0

    return success_response({
        "summary": {
            "students_on_route": data["students_using_transport"],
            "routes_on_time": f"{data['total_routes']} / {data['total_routes']}",
            "schedule_adherence": "100.0%",
            "vehicles_in_service": f"{running_buses} / {data['total_buses']}",
            "under_maintenance": 0,
            "transport_alerts": 0,
        },
        "route_distribution": route_distribution,
        "total_students": data["students_using_transport"],
        "activity": {
            "trips_completed": completed_buses,
            "trips_running": running_buses,
            "delayed_trips": delayed_buses,
            "vehicles_under_maintenance": 0,
        },
    })


@transport_router.get("/vehicles")
async def get_vehicles(session: AsyncSession = Depends(get_db)):
    items = await bus_service.list(session)
    return success_response(items)


@transport_router.get("/vehicles/{item_id}")
async def get_vehicle(item_id: UUID, session: AsyncSession = Depends(get_db)):
    item = await bus_service.get(session, item_id)
    return success_response(item)


@transport_router.post("/vehicles", status_code=status.HTTP_201_CREATED)
async def create_vehicle(
    payload: BusCreate,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_admin(current_user)
    item = await bus_service.create(session, payload.model_dump())
    return success_response(item, message="Vehicle created successfully")


@transport_router.put("/vehicles/{item_id}")
async def update_vehicle(
    item_id: UUID,
    payload: BusUpdate,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_admin(current_user)
    item = await bus_service.update(session, item_id, payload.model_dump(exclude_unset=True))
    return success_response(item, message="Vehicle updated successfully")


@transport_router.delete("/vehicles/{item_id}")
async def delete_vehicle(
    item_id: UUID,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_admin(current_user)
    await bus_service.delete(session, item_id)
    return success_response(message="Vehicle deleted successfully")


@transport_router.get("/routes")
async def get_transport_routes(session: AsyncSession = Depends(get_db)):
    items = await route_service.list(session)
    return success_response(items)


@transport_router.get("/routes/{item_id}")
async def get_transport_route(item_id: UUID, session: AsyncSession = Depends(get_db)):
    item = await route_service.get(session, item_id)
    return success_response(item)


@transport_router.post("/routes", status_code=status.HTTP_201_CREATED)
async def create_transport_route(
    payload: RouteCreate,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_admin(current_user)
    item = await route_service.create(session, payload.model_dump())
    return success_response(item, message="Route created successfully")


@transport_router.put("/routes/{item_id}")
async def update_transport_route(
    item_id: UUID,
    payload: RouteUpdate,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_admin(current_user)
    item = await route_service.update(session, item_id, payload.model_dump(exclude_unset=True))
    return success_response(item, message="Route updated successfully")


@transport_router.delete("/routes/{item_id}")
async def delete_transport_route(
    item_id: UUID,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_admin(current_user)
    await route_service.delete(session, item_id)
    return success_response(message="Route deleted successfully")


@transport_router.get("/drivers")
async def get_drivers(session: AsyncSession = Depends(get_db)):
    items = await driver_service.list(session)
    return success_response(items)


@transport_router.get("/drivers/{item_id}")
async def get_driver(item_id: UUID, session: AsyncSession = Depends(get_db)):
    item = await driver_service.get(session, item_id)
    return success_response(item)


@transport_router.post("/drivers", status_code=status.HTTP_201_CREATED)
async def create_driver(
    payload: DriverCreate,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_admin(current_user)
    item = await driver_service.create(session, payload.model_dump())
    return success_response(item, message="Driver created successfully")


@transport_router.put("/drivers/{item_id}")
async def update_driver(
    item_id: UUID,
    payload: DriverUpdate,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_admin(current_user)
    item = await driver_service.update(session, item_id, payload.model_dump(exclude_unset=True))
    return success_response(item, message="Driver updated successfully")


@transport_router.delete("/drivers/{item_id}")
async def delete_driver(
    item_id: UUID,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_admin(current_user)
    await driver_service.delete(session, item_id)
    return success_response(message="Driver deleted successfully")


@transport_router.post("/drivers/assign")
async def assign_driver(
    payload: DriverCreate,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_admin(current_user)
    if payload.bus_id is not None:
        bus = await session.get(Bus, payload.bus_id)
        if bus is None:
            raise APIException(status_code=status.HTTP_404_NOT_FOUND, message="Bus not found")
    item = await driver_service.create(session, payload.model_dump())
    return success_response(item, message="Driver assigned successfully")


@transport_router.get("/student-transport")
async def get_student_transport_allocations(session: AsyncSession = Depends(get_db)):
    result = await session.execute(
        select(StudentTransport).options(
            selectinload(StudentTransport.student),
            selectinload(StudentTransport.bus),
            selectinload(StudentTransport.route),
        )
    )
    allocations = result.scalars().all()
    data = []
    for alloc in allocations:
        data.append({
            "id": str(alloc.id),
            "student_id": str(alloc.student_id),
            "bus_id": str(alloc.bus_id),
            "route_id": str(alloc.route_id),
            "stop_point": alloc.stop_point,
            "student_name": f"{alloc.student.first_name or ''} {alloc.student.last_name or ''}".strip() if alloc.student else "",
            "bus_number": alloc.bus.bus_number if alloc.bus else "",
            "route_name": alloc.route.route_name if alloc.route else "",
            "created_at": alloc.created_at.isoformat() if alloc.created_at else "",
        })
    return success_response(data)


@transport_router.post("/student-transport", status_code=status.HTTP_201_CREATED)
async def create_student_transport_allocation(
    payload: StudentTransportCreate,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_admin(current_user)
    allocation = await student_transport_service.create_transport(session, payload.model_dump())
    return success_response(allocation, message="Student assigned to transport successfully")


@transport_router.delete("/student-transport/{item_id}")
async def delete_student_transport_allocation(
    item_id: UUID,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_admin(current_user)
    await student_transport_service.delete_transport(session, item_id)
    return success_response(message="Student transport allocation removed successfully")


@transport_router.get("/trips")
async def get_trips(session: AsyncSession = Depends(get_db)):
    from sqlalchemy.orm import selectinload

    result = await session.execute(
        select(StudentTransport).options(
            selectinload(StudentTransport.student),
            selectinload(StudentTransport.bus),
            selectinload(StudentTransport.route),
        )
    )
    allocations = result.scalars().all()

    trips: dict[str, dict] = {}
    for alloc in allocations:
        key = f"{alloc.bus_id}:{alloc.route_id}"
        if key not in trips:
            trips[key] = {
                "bus_id": str(alloc.bus_id),
                "route_id": str(alloc.route_id),
                "bus_number": alloc.bus.bus_number if alloc.bus else "",
                "route_name": alloc.route.route_name if alloc.route else "",
                "start_point": alloc.route.start_point if alloc.route else "",
                "end_point": alloc.route.end_point if alloc.route else "",
                "stop_point": alloc.stop_point,
                "students": 0,
                "student_names": [],
            }
        trips[key]["students"] += 1
        if alloc.student:
            name = f"{alloc.student.first_name or ''} {alloc.student.last_name or ''}".strip()
            if name:
                trips[key]["student_names"].append(name)

    trip_list = []
    for i, (key, trip) in enumerate(trips.items()):
        driver_name = ""
        driver_result = await session.execute(select(Driver).where(Driver.bus_id == trip["bus_id"]))
        driver = driver_result.scalar_one_or_none()
        if driver:
            driver_name = driver.driver_name

        route_colors = ["#10b981", "#3b82f6", "#eab308", "#ef4444", "#f97316", "#7c3aed"]
        trip_list.append({
            "id": f"trip-{i + 1}",
            "routeId": trip["route_id"][:8],
            "routeName": trip["route_name"],
            "routeColor": route_colors[i % len(route_colors)],
            "stops": f"{trip['start_point']} → {trip['end_point']}",
            "vehicleNo": trip["bus_number"],
            "driverName": driver_name,
            "pickupTime": "07:15 AM",
            "dropTime": "03:15 PM",
            "students": trip["students"],
            "status": "Running",
        })

    return success_response(trip_list)
