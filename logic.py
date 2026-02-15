from classes import *

from typing import Dict, Any

import httpx
from fastapi import HTTPException
from uvicorn.server import logger

def is_fit(item: Item, cell: Cell) -> bool:
    if not item.dimensions.fits_in(cell.dimensions):
        return False

    if item.dimensions.volume() > cell.free_volume():
        return False

    return True


def score_cell(item: Item, cell: Cell) -> float:
    score = item.dimensions.volume() * 100 / cell.free_volume()

    if item.requires_iot_cell:
        if cell.iot is None or not cell.iot.is_work or cell.iot.temperature_status != item.temperature_status:
            score = -float("inf")
            return score

    if item.weight_kg is not None and cell.max_load_kg is not None:
        if cell.current_load_kg + item.weight_kg > cell.max_load_kg:
            score = -float("inf")

    return score


def choose_best_cell(req: PlacementRequest) -> List[Tuple[Cell, float]]:
    candidates: List[Tuple[Cell, float]] = []
    rejected: Dict[str, str] = {}

    for cell in req.cells:
        if not is_fit(req.item, cell):
            rejected[cell.cell_id] = "товар не подходит по размеру"
            continue

        score = score_cell(req.item, cell)
        if score < 0:
            rejected[cell.cell_id] = "товар не подходит по весу или условиям хранения"
        else:
            candidates.append((cell, score))

    debug = {
        "candidates_count": len(candidates),
        "rejected_count": len(rejected),
        "top5": ([{"cell_id": c.cell_id, "score": s} for c, s in candidates])[:5],
        "rejected": rejected,
    }

    logger.info(debug)

    if not candidates:
        raise HTTPException(
            status_code=422,
            detail={
                "error": "NO_SUITABLE_CELL",
                "message": "Нет подходящих ячеек для расположения товара.",
                "rejected": rejected,
            },
        )

    candidates = sorted(candidates, key=lambda x: x[1], reverse=True)

    return candidates


async def send_to_task_api(payload: Dict[str, Any]) -> bool:
    if not TASK_API_URL:
        return False
    try:
        async with httpx.AsyncClient() as client:
            r = await client.post(TASK_API_URL, json=payload)
            r.raise_for_status()
        return True
    except Exception:
        return False
