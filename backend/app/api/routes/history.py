from fastapi import APIRouter, HTTPException, status, Query
from app.services.history_service import history_service
from app.schemas.prediction import HistoryListResponse, HistoryItem

router = APIRouter(prefix="/history", tags=["History"])

@router.get("", response_model=HistoryListResponse)
async def get_screening_history(limit: int = Query(50, ge=1, le=200)):
    """
    Returns paginated list of prior screening records (both valid and non-prediction outcomes).
    """
    records = history_service.get_all(limit=limit)
    items = []
    for rec in records:
        sid = rec.get("screening_id") or rec.get("id")
        items.append(HistoryItem(
            screening_id=sid,
            timestamp=rec.get("timestamp", ""),
            filename=rec.get("filename", "unknown"),
            status=rec.get("status", "VALID"),
            model_version=rec.get("model_version", "b3-aptos-epoch7"),
            predicted_class=rec.get("predicted_class"),
            predicted_class_name=rec.get("predicted_class_name"),
            confidence=rec.get("confidence"),
            referable_probability=rec.get("referable_probability"),
            is_referable=rec.get("is_referable"),
            probabilities=rec.get("probabilities"),
            quality=rec.get("quality"),
            heatmap_url=rec.get("heatmap_url"),
            overlay_url=rec.get("overlay_url"),
            original_url=rec.get("original_url")
        ))
    return HistoryListResponse(
        total=len(items),
        items=items
    )

@router.get("/{screening_id}", response_model=HistoryItem)
async def get_history_detail(screening_id: str):
    """
    Retrieves a single screening record by ID.
    """
    record = history_service.get_by_id(screening_id)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Screening record '{screening_id}' not found."
        )
    sid = record.get("screening_id") or record.get("id")
    return HistoryItem(
        screening_id=sid,
        timestamp=record.get("timestamp", ""),
        filename=record.get("filename", "unknown"),
        status=record.get("status", "VALID"),
        model_version=record.get("model_version", "b3-aptos-epoch7"),
        predicted_class=record.get("predicted_class"),
        predicted_class_name=record.get("predicted_class_name"),
        confidence=record.get("confidence"),
        referable_probability=record.get("referable_probability"),
        is_referable=record.get("is_referable"),
        probabilities=record.get("probabilities"),
        quality=record.get("quality"),
        heatmap_url=record.get("heatmap_url"),
        overlay_url=record.get("overlay_url"),
        original_url=record.get("original_url")
    )
