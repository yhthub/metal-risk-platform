"""Authenticated table inspection/conversion; source data is never persisted."""
from urllib.parse import quote

from fastapi import APIRouter, File, Form, HTTPException, Response, UploadFile
from fastapi.concurrency import run_in_threadpool

from ..services.data_cleaning_service import (
    CleaningError, MAX_FILE_BYTES, export_table, get_cleaning_schema,
    inspect_table, preview_table,
)
from ..services.table_processing_capacity import run_table_processing, TableProcessingBusy


router = APIRouter(prefix="/api/datainput/cleaning", tags=["数据清洗与格式转换"])
PRIVATE_HEADERS = {"Cache-Control": "no-store", "X-Content-Type-Options": "nosniff"}


async def _file_bytes(file: UploadFile) -> tuple[bytes, str]:
    try:
        content = await file.read(MAX_FILE_BYTES + 1)
        if len(content) > MAX_FILE_BYTES:
            raise HTTPException(status_code=413, detail="文件超过 25 MB 限制")
        return content, file.filename or "dataset.csv"
    finally:
        await file.close()


async def _convert(function, *args, guard_capacity=True):
    try:
        if guard_capacity:
            return await run_in_threadpool(run_table_processing, function, *args)
        return await run_in_threadpool(function, *args)
    except TableProcessingBusy as exc:
        raise HTTPException(status_code=429, detail=str(exc), headers={"Retry-After": "5"}) from exc
    except CleaningError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc


@router.get("/schema")
async def schema(outcome_id: str = "blood_pressure"):
    return await _convert(get_cleaning_schema, outcome_id, guard_capacity=False)


@router.post("/inspect")
async def inspect(response: Response, file: UploadFile = File(...)):
    response.headers.update(PRIVATE_HEADERS)
    content, filename = await _file_bytes(file)
    return await _convert(inspect_table, content, filename)


@router.post("/preview")
async def preview(response: Response, file: UploadFile = File(...), options: str = Form(...)):
    response.headers.update(PRIVATE_HEADERS)
    content, filename = await _file_bytes(file)
    return await _convert(preview_table, content, filename, options)


@router.post("/export")
async def export(file: UploadFile = File(...), options: str = Form(...)):
    content, filename = await _file_bytes(file)
    payload, download_name, result = await _convert(export_table, content, filename, options)
    headers = {**PRIVATE_HEADERS,
               "Content-Disposition": "attachment; filename=cleaned_dataset.csv; filename*=UTF-8''" + quote(download_name),
               "X-Cleaning-System-Ready": "true" if result["system_ready"] else "false",
               "X-Cleaning-Row-Count": str(result["total_rows"])}
    return Response(content=payload, media_type="text/csv; charset=utf-8", headers=headers)
