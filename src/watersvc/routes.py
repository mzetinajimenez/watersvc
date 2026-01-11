"""API route handlers."""

from fastapi import APIRouter

router = APIRouter()


@router.get("/data")
def get_sample_data():
    return {
        "data": [
            {"id": 1, "name": "Sample Item 1", "value": 100},
            {"id": 2, "name": "Sample Item 2", "value": 200},
            {"id": 3, "name": "Sample Item 3", "value": 300},
        ],
        "total": 3,
        "timestamp": "2024-01-01T00:00:00Z",
    }


@router.get("/items/{item_id}")
def get_item(item_id: int):
    return {
        "item": {"id": item_id, "name": "Sample Item " + str(item_id), "value": item_id * 100},
        "timestamp": "2024-01-01T00:00:00Z",
    }
