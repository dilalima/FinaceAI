"""CSV import response schemas."""

from pydantic import BaseModel


class ImportErrorItem(BaseModel):
    row: int
    error: str


class ImportResult(BaseModel):
    imported: int
    skipped_duplicates: int
    errors: list[ImportErrorItem]
