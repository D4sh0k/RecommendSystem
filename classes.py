from enum import Enum
from itertools import permutations
from typing import List, Optional, Tuple

from pydantic import BaseModel, Field

TASK_API_URL = None

class TemperatureStatus(str, Enum):
    room = "room"
    high = "high"
    low = "low"


class Dimensions(BaseModel):
    length: float = Field(..., gt=0)
    width: float = Field(..., gt=0)
    height: float = Field(..., gt=0)
    can_rotate: bool = True

    def volume(self) -> float:
        return self.length * self.width * self.height

    def orientations(self) -> List[Tuple[float, float, float]]:
        dims = (self.length, self.width, self.height)
        if not self.can_rotate:
            return [dims]
        else:
            return sorted(set(permutations(dims)))

    def fits_in(self, other: "Dimensions") -> bool:
        for l, w, h in self.orientations():
            if l <= other.length and w <= other.width and h <= other.height:
                return True
        return False


    def best_orientation_for(self, other: "Dimensions") -> Optional[Tuple[float, float, float]]:
        best: Optional[Tuple[float, float, float]] = None
        best_slack = float("inf")

        for l, w, h in self.orientations():
            if l <= other.length and w <= other.width and h <= other.height:
                slack = (other.length - l) + (other.width - w) + (other.height - h)
                if slack < best_slack:
                    best_slack = slack
                    best = (l, w, h)

        return best


class IoTCellData(BaseModel):
    temperature: Optional[float] = None
    temperature_status: Optional[TemperatureStatus] = Field(default=TemperatureStatus.room)
    wet: Optional[float] = Field(default=None, ge=0, le=100)

    is_work: Optional[bool] = True


class Cell(BaseModel):
    cell_id: str = Field(..., min_length=1)
    dimensions: Dimensions
    max_load_kg: Optional[float] = Field(default=None, gt=0)

    used_volume: float = Field(default=0, ge=0)
    current_load_kg: float = Field(default=0, ge=0)

    iot: Optional[IoTCellData] = None

    def free_volume(self) -> float:
        return max(self.dimensions.volume() - self.used_volume, 0.0)


class Item(BaseModel):
    item_id: Optional[str] = None
    dimensions: Dimensions
    weight_kg: Optional[float] = Field(default=None, gt=0)

    requires_iot_cell: bool = False
    temperature_status: Optional[TemperatureStatus] = Field(default=TemperatureStatus.room)


class PlacementRequest(BaseModel):
    item: Item
    cells: List[Cell] = Field(..., min_length=1)


class PlacementResponse(BaseModel):
    placement_id: str
    cell_id: str
    placements: List[Tuple[Cell, float]] = Field(..., min_length=1)