from typing import TypedDict


class MappingRow(TypedDict, total=False):
    BayName: str
    BayCX: str
    BayCY: str
    EquipID: str
    Item: str
    Category: str
    Quantity: str


class BaySummary(TypedDict):
    cx: float
    cy: float
    slab_in: float
    total_weight: float


class MechService(TypedDict, total=False):
    type: str
    value: float
    units: str
    assumption: str
