from typing import List
from fastapi import APIRouter, HTTPException, status, Query
from app.services.history_service import history_service
from app.schemas.prediction import HistoryListResponse, HistoryItem

router = APIRouter(prefix="/history", tags=["History"])

@router.get("", response_model=HistoryListResponse)
async def get_screening_history(limit: int = Query(50, ge=1, le=200)):
    records = history_service.get_all(limit=limit)
    return HistoryListResponse(
        total=len(records),
        items=[HistoryItem(**rec) for rec in records]
    )

@router.get("/{prediction_id}", response_model=HistoryItem)
async def get_history_detail(prediction_id: str):
    record = history_service.get_by_id(prediction_id)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Screening record '{prediction_id}' not found."
        )
    return HistoryItem(**record)
