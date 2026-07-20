from typing import List, Optional

from pydantic import BaseModel


class SiteStat(BaseModel):
    site: str
    site_name: str
    count: int
    percentage: float


class StatusStat(BaseModel):
    status: str
    label: str
    count: int


class ExtraStat(BaseModel):
    key: str
    label: str
    count: int
    percentage: Optional[float] = None


class AdminOverviewResponse(BaseModel):
    entity: str
    title: str
    description: str
    total: int
    by_site: List[SiteStat]
    by_status: List[StatusStat]
    extra: List[ExtraStat] = []
