"""
Schemas for Excel Import
PASO 6
"""
from pydantic import BaseModel
from typing import List, Optional


class ImportRowResult(BaseModel):
    """Result for a single row import"""
    row: int
    status: str  # "imported", "failed", "skipped"
    warnings: List[str] = []
    errors: List[str] = []
    account_name: Optional[str] = None
    opportunity_id: Optional[str] = None


class ImportResponse(BaseModel):
    """Response after import"""
    import_id: str
    dry_run: bool
    total_rows: int
    imported_rows: int
    failed_rows: int
    skipped_rows: int
    warnings_count: int
    errors_count: int
    items: List[ImportRowResult]
    file_saved: Optional[str] = None
    report_saved: Optional[str] = None


class ImportReportResponse(BaseModel):
    """Saved import report"""
    import_id: str
    dry_run: bool
    total_rows: int
    imported_rows: int
    failed_rows: int
    skipped_rows: int
    warnings_count: int
    errors_count: int
    items: List[ImportRowResult]
    timestamp: str
