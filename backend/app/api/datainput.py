from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Response
from typing import List, Dict, Any
from ..models.schemas import (
    IndividualData, BatchImportResponse, DataStatistics,
    VisualizationData, ApiResponse
)
from ..services.data_service import (
    save_individual_data, import_batch_file,
    get_data_statistics, get_visualization_data,
    get_all_records, get_record_by_id,
    get_outcome_configs, get_dataset_analysis,
    DatasetValidationError, MAX_UPLOAD_SIZE
)
from ..services.public_demo_service import get_public_demo_metadata, import_public_demo, PublicDemoError

router = APIRouter(prefix="/api/datainput", tags=["数据接入"])
DEMO_RESPONSE_HEADERS = {"Cache-Control": "no-store", "X-Content-Type-Options": "nosniff"}


@router.get("/demo", response_model=Dict[str, Any], summary="获取 NHANES 固定公开体验样本来源")
async def get_group_demo(response: Response):
    response.headers.update(DEMO_RESPONSE_HEADERS)
    try:
        return get_public_demo_metadata()
    except PublicDemoError as exc:
        raise HTTPException(status_code=503, detail=str(exc), headers=DEMO_RESPONSE_HEADERS)


@router.post("/demo/import", response_model=Dict[str, Any], summary="导入独立 NHANES 公开样本并真实分析")
async def import_group_demo(response: Response):
    response.headers.update(DEMO_RESPONSE_HEADERS)
    try:
        return await import_public_demo()
    except PublicDemoError as exc:
        raise HTTPException(status_code=503, detail=str(exc), headers=DEMO_RESPONSE_HEADERS)
    except DatasetValidationError as exc:
        headers = {**DEMO_RESPONSE_HEADERS, **({"Retry-After": "5"} if exc.status_code == 429 else {})}
        raise HTTPException(status_code=exc.status_code, detail={"message": str(exc), "missing_columns": exc.missing_columns}, headers=headers)


@router.get("/outcomes", response_model=List[Dict[str, Any]], summary="获取预测结局配置")
async def list_outcome_configs():
    """获取可选择的预测结局，以及该结局要求的暴露和混杂因素。"""
    return get_outcome_configs()


@router.post("/single", response_model=ApiResponse, summary="单人数据录入")
async def create_individual_data(data: IndividualData):
    """
    录入单个工人的职业暴露数据

    - **id**: 工号，如 SZ-102
    - **gender**: 性别 (male/female)
    - **age**: 年龄
    - **work_years**: 暴露工龄(年)
    - **job**: 工种 (smelting/mining/welding/other)
    - **pb, cd, hg, th, li, cr, ni, co**: 8种核心重金属暴露指标
    - **as_val, rn**: 伴生非金属与标志物
    """
    result = await save_individual_data(data)
    return result


@router.post("/batch", response_model=BatchImportResponse, summary="群体数据批量导入")
async def import_batch_data(
    file: UploadFile = File(...),
    outcome_id: str = Form("blood_pressure"),
):
    """
    批量导入群体监测数据 (CSV/XLSX)

    - 支持 .csv 和 .xlsx 格式
    - 根据 outcome_id 校验结局、暴露和混杂因素字段
    - 血压结局限定18岁及以上，且收缩压、舒张压各至少2次有效读数
    """
    try:
        if not (file.filename or '').lower().endswith(('.csv', '.xlsx')):
            raise HTTPException(status_code=400, detail="仅支持 CSV 和 XLSX 格式文件")
        content = await file.read(MAX_UPLOAD_SIZE + 1)
        if len(content) > MAX_UPLOAD_SIZE:
            raise DatasetValidationError("文件超过 25 MB 限制", status_code=413)
        result = await import_batch_file(content, file.filename, outcome_id)
        return result
    except DatasetValidationError as e:
        raise HTTPException(
            status_code=e.status_code,
            detail={
                "message": str(e),
                "missing_columns": e.missing_columns,
            },
            headers={"Retry-After": "5"} if e.status_code == 429 else None,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="文件导入失败，请检查服务存储状态后重试") from e
    finally:
        await file.close()


@router.get("/analysis/{file_id}", response_model=Dict[str, Any], summary="获取群体数据统计分析")
async def get_analysis(file_id: str):
    """获取上传文件对应的描述性统计、人口学分布和图表数据。"""
    try:
        return await get_dataset_analysis(file_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/statistics/{file_id}", response_model=DataStatistics, summary="获取数据统计信息")
async def get_statistics(file_id: str):
    """
    获取批量导入数据的统计信息

    - **file_id**: 文件ID（批量导入时返回）
    """
    try:
        result = await get_data_statistics(file_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/visualization/{file_id}", response_model=VisualizationData, summary="获取可视化数据")
async def get_visualization(file_id: str):
    """
    获取数据可视化所需的统计数据

    - 婚姻状况分布
    - 学历分布
    - 收入分布
    - 金属浓度统计
    """
    try:
        result = await get_visualization_data(file_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/records", response_model=List[dict], summary="获取所有记录")
async def list_records():
    """获取所有单人录入的记录"""
    return await get_all_records()


@router.get("/records/{record_id}", response_model=dict, summary="获取单条记录")
async def get_record(record_id: str):
    """根据工号获取单条记录"""
    record = await get_record_by_id(record_id)
    if record is None:
        raise HTTPException(status_code=404, detail=f"记录不存在: {record_id}")
    return record
