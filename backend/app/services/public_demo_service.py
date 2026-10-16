"""Fixed, allowlisted NHANES demo assets, independent of a user's local D drive."""
from __future__ import annotations

import csv
from copy import deepcopy
import hashlib
from io import StringIO
import json
from pathlib import Path
import re

from .data_service import OUTCOME_CONFIGS, _get_required_columns, import_batch_file, get_dataset_analysis

ASSET_DIR = Path(__file__).resolve().parents[1] / "data"
MANIFEST_NAME = "nhanes_public_demo.manifest.json"
DEMO_ID = "nhanes_2017_2018_public_adults_300"
SAMPLE_NAME = "NHANES_2017-2018_public_adults_300.csv"


class PublicDemoError(ValueError):
    pass


def _load_public_demo() -> tuple[dict, bytes]:
    try:
        manifest_path = ASSET_DIR / MANIFEST_NAME
        if manifest_path.stat().st_size > 64 * 1024:
            raise PublicDemoError("公开样本说明超过部署限制")
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        config = OUTCOME_CONFIGS["blood_pressure"]
        allowed = _get_required_columns(config) + config["survey_design_columns"]
        if (manifest.get("id") != DEMO_ID or manifest.get("sample_filename") != SAMPLE_NAME or
                manifest.get("columns") != allowed or manifest.get("rows") != 300 or
                manifest.get("outcome_id") != "blood_pressure"):
            raise PublicDemoError("公开样本与当前系统字段规范不一致，请重新准备部署样本")
        asset_path = ASSET_DIR / SAMPLE_NAME
        if asset_path.stat().st_size > 1024 * 1024:
            raise PublicDemoError("公开样本超过部署大小限制")
        content = asset_path.read_bytes()
        expected = manifest.get("sample_sha256", "")
        if not isinstance(expected, str) or not re.fullmatch(r"[0-9a-f]{64}", expected):
            raise PublicDemoError("公开样本说明缺少有效校验值")
        if hashlib.sha256(content).hexdigest() != expected or len(content) != manifest.get("sample_bytes"):
            raise PublicDemoError("公开样本完整性校验失败，未导入任何示例记录")
        rows = list(csv.reader(StringIO(content.decode("utf-8-sig"))))
        if not rows or rows[0] != allowed or len(rows) - 1 != 300 or any(len(row) != len(allowed) for row in rows[1:]):
            raise PublicDemoError("公开样本的字段或记录数校验失败")
        return manifest, content
    except PublicDemoError:
        raise
    except (OSError, ValueError, TypeError, KeyError) as exc:
        raise PublicDemoError("公开样本暂不可用，请确认随服务器部署了样本与来源说明") from exc


def get_public_demo_metadata() -> dict:
    manifest, _ = _load_public_demo()
    return deepcopy(manifest)


async def import_public_demo() -> dict:
    manifest, content = _load_public_demo()
    # Existing import generates a new independent ID; no user result is replaced.
    imported = await import_batch_file(content, SAMPLE_NAME, "blood_pressure", provenance=manifest)
    analysis = await get_dataset_analysis(imported.file_id)
    return {"import_result": imported.model_dump(), "analysis": analysis, "provenance": deepcopy(manifest)}
