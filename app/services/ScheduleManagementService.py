from typing import Dict, Tuple

from fastapi import HTTPException
from sqlalchemy.orm import Session

from configs.db import SessionLocals
from models.Schedules import Schedule
from repositories.ScheduleRepo import ScheduleRepo
from schemas.ClassSection import ScheduleResponse
from services.ClassSectionService import ClassSectionService


class ScheduleManagementService:
    @staticmethod
    def get_all_schedules() -> Tuple[list[ScheduleResponse], int]:
        sessions = ScheduleManagementService._open_all_sessions()
        items: list[ScheduleResponse] = []

        try:
            for session in sessions.values():
                schedules = (
                    ScheduleRepo.base_query(session)
                    .order_by(Schedule.MaLich.asc())
                    .all()
                )
                items.extend(ClassSectionService._build_schedule_response(session, item) for item in schedules)
            items.sort(key=lambda item: item.MaLich)
            return items, len(items)
        finally:
            ScheduleManagementService._close_sessions(sessions)

    @staticmethod
    def get_schedule_by_id(ma_lich: str) -> ScheduleResponse:
        sessions = ScheduleManagementService._open_all_sessions()

        try:
            _, session, schedule = ScheduleManagementService._find_schedule_context(sessions, ma_lich)
            return ClassSectionService._build_schedule_response(session, schedule)
        finally:
            ScheduleManagementService._close_sessions(sessions)

    @staticmethod
    def _find_schedule_context(sessions: Dict[str, Session], ma_lich: str) -> tuple[str, Session, Schedule]:
        schedule_code = ma_lich.upper()
        for site, session in sessions.items():
            schedule = ScheduleRepo.get_by_id(session, schedule_code)
            if schedule:
                return site, session, schedule
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Khong tim thay lich hoc voi ma: {schedule_code}",
        )

    @staticmethod
    def _open_all_sessions() -> Dict[str, Session]:
        return {site: session_factory() for site, session_factory in SessionLocals.items()}

    @staticmethod
    def _close_sessions(sessions: Dict[str, Session]) -> None:
        for session in sessions.values():
            session.close()
