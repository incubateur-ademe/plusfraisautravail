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


class PhenomenonAlert(BaseModel):
    id: str = Field(..., description="Météo-France phenomenon ID, e.g. '6' for canicule.")
    name: str = Field(..., description="Phenomenon slug, e.g. 'canicule', 'orages'.")
    day1: Severity
    day2: Severity


class DepartmentMeteoAlert(BaseModel):
    code: str = Field(..., description="Department code, e.g. '75', '2A'.")
    name: str = Field(..., description="Department name, e.g. 'Paris'.")
    phenomena: list[PhenomenonAlert] = Field(
        ..., description="Phenomena with at least one day at jaune or above."
    )


class MeteoSnapshot(BaseModel):
    active: bool = Field(
        ..., description="True iff at least one metropolitan dept has an active phenomenon."
    )
    departments: list[DepartmentMeteoAlert] = Field(
        default_factory=list,
        description=(
            "Metropolitan departments with at least one phenomenon at jaune or above. "
            "Sorted by code."
        ),
    )
    fetched_at: datetime
    source: str = "meteofrance.vigilance"


class ElectricityLevel(StrEnum):
    VERT = "vert"
    ORANGE = "orange"
    ROUGE = "rouge"


class ElectricityDayForecast(BaseModel):
    date: str = Field(..., description="ISO date (YYYY-MM-DD), local time.")
    level: ElectricityLevel
    code: int = Field(..., description="Raw RTE dvalue (1=vert, 2=orange, 3=rouge).")
    message: str | None = None


class ElectricitySnapshot(BaseModel):
    days: list[ElectricityDayForecast]
    currently_strained: bool = Field(
        ..., description="True if today's level is orange or rouge."
    )
    upcoming_strain: bool = Field(
        ..., description="True if any of the next 3 days is orange or rouge."
    )
    fetched_at: datetime
    source: str = "rte.ecowatt"


class SourceMeta(BaseModel):
    name: str
    last_refresh: datetime | None
    healthy: bool
