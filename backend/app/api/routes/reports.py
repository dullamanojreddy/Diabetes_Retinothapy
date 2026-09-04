from fastapi import APIRouter, HTTPException, status
from fastapi.responses import HTMLResponse, JSONResponse

from app.services.report_service import report_service
from app.services.history_service import history_service
from app.core.logging_config import logger

router = APIRouter(prefix="/reports", tags=["Reports"])

@router.get("/{screening_id}", response_class=HTMLResponse)
async def get_html_report(screening_id: str):
    """
    Retrieves and renders an automated annotated HTML screening report for a completed screening.
    Print-optimized for physical printing and PDF export via browser Print dialog.
    """
    record = history_service.get_by_id(screening_id)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Screening record '{screening_id}' not found."
        )

    html_content = report_service.generate_html_report(record)
    return HTMLResponse(content=html_content, status_code=status.HTTP_200_OK)

@router.get("/{screening_id}/json", response_class=JSONResponse)
async def get_json_report(screening_id: str):
    """
    Returns structured screening report telemetry for programmatic PDF generation or EMR integration.
    """
    record = history_service.get_by_id(screening_id)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Screening record '{screening_id}' not found."
        )

    return JSONResponse(content=record, status_code=status.HTTP_200_OK)
