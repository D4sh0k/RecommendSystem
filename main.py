from logic import *

import uuid

from fastapi import FastAPI

app = FastAPI(
    title="Рекомендация размещения товаров",
    version="1.0.0",
    description="API предназначено для повышения эффективности размещения, сокращения времени обработки и рационального использования складского пространства.",
)


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.post("/get_item_location", response_model=PlacementResponse)
async def get_item_location(req: PlacementRequest) -> PlacementResponse:
    top = choose_best_cell(req)

    best_cell, best_score = max(top, key=lambda x: x[1])

    placement_id = str(uuid.uuid4())

    task_payload = {
        "placement_id": placement_id,
        "cell_id": best_cell.cell_id,
        "item_id": req.item.item_id,
        "item_dimensions": req.item.dimensions.model_dump(),
        "item_weight_kg": req.item.weight_kg
    }

    await send_to_task_api(task_payload)

    return PlacementResponse(
        placement_id=placement_id,
        cell_id=best_cell.cell_id,
        placements=top
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8000
    )