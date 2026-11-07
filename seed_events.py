import asyncio
import uuid
from datetime import date, timedelta
from app.core.database import AsyncSessionLocal
from app.models.event_model import Event, AcademicCalendar
from app.models.user import User
from app.models.role import Role
from sqlalchemy import select

async def seed_events():
    async with AsyncSessionLocal() as session:
        # Find admin user for created_by
        admin_res = await session.execute(
            select(User).join(User.role).where(Role.role_name == "ADMIN").limit(1)
        )
        admin = admin_res.scalar_one_or_none()
        if not admin:
            # Fallback to any user
            any_res = await session.execute(select(User).limit(1))
            admin = any_res.scalar_one_or_none()
        
        if not admin:
            print("No admin user found to attribute events to.")
            return

        print(f"Using admin user: {admin.id} ({admin.username})")

        # Check existing events count
        existing_events = (await session.execute(select(Event))).scalars().all()
        if len(existing_events) > 0:
            print(f"Events already seeded ({len(existing_events)} present).")
        else:
            today = date.today()
            sample_events = [
                Event(
                    id=uuid.uuid4(),
                    event_name="Annual Science & Innovation Championship",
                    event_type="ACADEMIC",
                    description="Inter-school science competition, robotics demonstrations, and student innovation project exhibitions.",
                    start_date=today + timedelta(days=3),
                    end_date=today + timedelta(days=4),
                    venue="Campus Auditorium & Science Wings",
                    created_by=admin.id,
                ),
                Event(
                    id=uuid.uuid4(),
                    event_name="Annual Track & Field Sports Championship",
                    event_type="SPORTS",
                    description="Inter-house track races, relay championships, long jump, shot put, and annual athletic awards ceremony.",
                    start_date=today + timedelta(days=10),
                    end_date=today + timedelta(days=12),
                    venue="School Sports Complex & Athletic Ground",
                    created_by=admin.id,
                ),
                Event(
                    id=uuid.uuid4(),
                    event_name="Tarang Cultural Fest & Arts Gala",
                    event_type="CULTURAL",
                    description="Showcasing musical bands, classical and contemporary dance performances, drama, and fine arts gallery.",
                    start_date=today + timedelta(days=18),
                    end_date=today + timedelta(days=19),
                    venue="Central Amphitheater",
                    created_by=admin.id,
                ),
                Event(
                    id=uuid.uuid4(),
                    event_name="Pre-Board Exam Orientation & Masterclass",
                    event_type="WORKSHOP",
                    description="Focused masterclasses covering exam pattern analysis, time management strategies, and subject revision plans.",
                    start_date=today + timedelta(days=24),
                    end_date=today + timedelta(days=24),
                    venue="Audio-Visual Conference Hall",
                    created_by=admin.id,
                ),
                Event(
                    id=uuid.uuid4(),
                    event_name="Winter Carnival & Student Club Fair",
                    event_type="CELEBRATION",
                    description="Annual winter carnival featuring interactive student club booths, food stalls, robotics games, and charity drives.",
                    start_date=today + timedelta(days=32),
                    end_date=today + timedelta(days=33),
                    venue="Main Campus Lawn",
                    created_by=admin.id,
                ),
                Event(
                    id=uuid.uuid4(),
                    event_name="Inter-School AI & Coding Hackathon",
                    event_type="COMPETITION",
                    description="24-hour coding challenge focused on designing smart campus utilities, AI applications, and accessible technology.",
                    start_date=today + timedelta(days=45),
                    end_date=today + timedelta(days=46),
                    venue="Computer Science Lab 1 & 2",
                    created_by=admin.id,
                ),
                Event(
                    id=uuid.uuid4(),
                    event_name="Term 2 Mid-Semester Examinations",
                    event_type="EXAMINATION",
                    description="Comprehensive mid-term evaluation across all standard academic subjects and practical assessments.",
                    start_date=today + timedelta(days=55),
                    end_date=today + timedelta(days=62),
                    venue="Classrooms & Examination Blocks",
                    created_by=admin.id,
                ),
            ]
            session.add_all(sample_events)
            await session.commit()
            print(f"Successfully seeded {len(sample_events)} events.")

        # Check existing calendar entries
        existing_cal = (await session.execute(select(AcademicCalendar))).scalars().all()
        if len(existing_cal) > 0:
            print(f"Academic Calendar entries already seeded ({len(existing_cal)} present).")
        else:
            today = date.today()
            sample_calendar = [
                AcademicCalendar(
                    id=uuid.uuid4(),
                    title="Annual Science & Innovation Fest",
                    event_type="EVENT",
                    start_date=today + timedelta(days=3),
                    end_date=today + timedelta(days=4),
                    description="Campus-wide exhibition of science and tech models.",
                    is_holiday=False,
                ),
                AcademicCalendar(
                    id=uuid.uuid4(),
                    title="Annual Sports Day Meet",
                    event_type="EVENT",
                    start_date=today + timedelta(days=10),
                    end_date=today + timedelta(days=12),
                    description="Inter-house track and field athletic tournaments.",
                    is_holiday=False,
                ),
                AcademicCalendar(
                    id=uuid.uuid4(),
                    title="Winter Break / School Holiday",
                    event_type="HOLIDAY",
                    start_date=today + timedelta(days=35),
                    end_date=today + timedelta(days=44),
                    description="School closed for winter recess. Reopens after new year.",
                    is_holiday=True,
                ),
                AcademicCalendar(
                    id=uuid.uuid4(),
                    title="Term 2 Mid-Semester Examinations",
                    event_type="EXAM",
                    start_date=today + timedelta(days=55),
                    end_date=today + timedelta(days=62),
                    description="Formal written assessment examinations.",
                    is_holiday=False,
                ),
                AcademicCalendar(
                    id=uuid.uuid4(),
                    title="National Republic Day Celebration",
                    event_type="HOLIDAY",
                    start_date=today + timedelta(days=68),
                    end_date=today + timedelta(days=68),
                    description="Flag hoisting ceremony in the morning; national holiday.",
                    is_holiday=True,
                ),
            ]
            session.add_all(sample_calendar)
            await session.commit()
            print(f"Successfully seeded {len(sample_calendar)} academic calendar entries.")

if __name__ == "__main__":
    asyncio.run(seed_events())
