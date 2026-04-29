from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class Severity(StrEnum):
    VERT = "vert"
    JAUNE = "jaune"
    ORANGE = "orange"
    ROUGE = "rouge"


COLOR_ID_TO_SEVERITY: dict[int, Severity] = {
    1: Severity.VERT,
    2: Severity.JAUNE,
    3: Severity.ORANGE,
    4: Severity.ROUGE,
}


class DepartmentAlert(BaseModel):
    code: str = Field(..., description="Department code, e.g. '75', '2A'.")
    day1: Severity
    day2: Severity


class HeatwaveSnapshot(BaseModel):
    phenomenon: str = "canicule"
    phenomenon_id: str = "8"
    departments: list[DepartmentAlert]
    fetched_at: datetime
    source: str = "meteofrance.vigilance"


class SourceMeta(BaseModel):
    name: str
    last_refresh: datetime | None
    healthy: bool
