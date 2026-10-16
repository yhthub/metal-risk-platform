"""Copy only released NHANES inference assets, refusing conflicting files.

Does not train, open raw participant data, mutate source files, or contact a server.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from pathlib import Path

RUN_ID = "nhanes_12outcomes_targeted_20261016_005"
PROJECT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE = Path("E:/NHANES_XGBoost_Targeted_2009-2018_20261016_v5")


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest()


def same_or_create(path: Path, content: bytes) -> None:
    if path.is_symlink():
        raise ValueError(f"Symlink destination is not allowed: {path}")
    if path.exists():
        if path.read_bytes() != content:
            raise ValueError(f"Conflicting existing file, refusing overwrite: {path}")
        return
    with path.open("xb") as stream:
        stream.write(content)


def prepare(source: Path, destination: Path) -> dict:
    source = source.resolve(strict=True)
    destination = destination.absolute()
    expected = PROJECT / "models" / "nhanes_v5"
    if destination != expected or destination.resolve() != expected:
        raise ValueError("Only the project's new models/nhanes_v5 destination is allowed")
    released = source / "04_models_cpu_optimized"
    hashes_path = source / "03_metadata" / "PUBLISHED_MODEL_HASHES.json"
    published = json.loads(hashes_path.read_text(encoding="utf-8"))
    published_lookup = {
        (entry["profile"], entry["target"], entry["name"]): entry["sha256"]
        for entry in published
    }
    registry_path = released / "registry.json"
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    if registry.get("run_id") != RUN_ID or registry.get("status") != "COMPLETE":
        raise ValueError("Source registry is not the completed v5 release")
    if registry.get("model_count") != 24 or len(registry.get("results", [])) != 24:
        raise ValueError("Expected exactly 24 full/basic model cards")
    files = {"registry.json": digest(registry_path)}
    component_count = 0
    for entry in registry["results"]:
        profile, target = entry["profile"], entry["target"]
        if profile not in ("full", "basic") or Path(target).name != target:
            raise ValueError("Unsafe profile/target")
        relative_card = f"{profile}/{target}/MODEL_CARD.json"
        card_path = released / relative_card
        card = json.loads(card_path.read_text(encoding="utf-8"))
        if (card.get("run_id"), card.get("profile"), card.get("target")) != (RUN_ID, profile, target):
            raise ValueError(f"Model card identity mismatch: {relative_card}")
        files[relative_card] = digest(card_path)
        for component in card["components"]:
            name = Path(component["model_file"]).name
            if Path(name).suffix not in (".ubj", ".cbm") or not name.startswith("component_"):
                raise ValueError(f"Unexpected model file: {name}")
            relative = f"{profile}/{target}/{name}"
            model_path = released / relative
            actual = digest(model_path)
            expected_hash = published_lookup.get((profile, target, name))
            if not expected_hash or actual != expected_hash or actual != component["sha256"]:
                raise ValueError(f"Released model hash mismatch: {relative}")
            files[relative] = actual
            component_count += 1
    if component_count != 24 or len(files) != 49:
        raise ValueError("Unexpected inference inventory; expected registry + 24 cards + 24 components")
    # Preflight every destination before copying any files.
    for relative, expected_hash in files.items():
        dest = destination / relative
        if dest.resolve().is_relative_to(destination) is False or dest.is_symlink():
            raise ValueError(f"Unsafe destination: {dest}")
        if dest.exists() and digest(dest) != expected_hash:
            raise ValueError(f"Conflicting existing model file: {dest}")
    destination.mkdir(parents=True, exist_ok=True)
    for relative, expected_hash in files.items():
        src, dest = released / relative, destination / relative
        dest.parent.mkdir(parents=True, exist_ok=True)
        if not dest.exists():
            with src.open("rb") as incoming, dest.open("xb") as outgoing:
                shutil.copyfileobj(incoming, outgoing)
        if digest(dest) != expected_hash:
            raise ValueError(f"Post-copy mismatch: {relative}")
    integrity = {"run_id": RUN_ID, "files": files}
    receipt = {
        "run_id": RUN_ID,
        "source_package": str(source),
        "source_published_model_hashes_sha256": digest(hashes_path),
        "asset_count": len(files),
        "model_count": component_count,
        "copied_bytes": sum((destination / name).stat().st_size for name in files),
        "source_models_verified_against_published_hashes": True,
        "source_model_cards_verified_against_component_hashes": True,
        "destination_hashes_verified": True,
        "training_or_participant_csv_copied": False,
        "source_files_changed": False,
    }
    for name, data in (("integrity.json", integrity), ("LOCAL_ASSET_RECEIPT.json", receipt)):
        same_or_create(destination / name, (json.dumps(data, indent=2, ensure_ascii=False) + "\n").encode("utf-8"))
    return receipt


def smoke(destination: Path) -> dict:
    """Native model compatibility check on synthetic inputs only; never calls fit."""
    import importlib.metadata
    import math

    import numpy as np
    import pandas as pd
    import xgboost as xgb
    from catboost import CatBoostRegressor

    # Import the actual backend/native dependencies, without importing an API
    # that might initiate optional retrieval clients or network activity.
    for module in ("fastapi", "pandas", "numpy", "plotly", "scipy", "sklearn"):
        __import__(module)
    if xgb.__version__ != "3.4.1":
        raise ValueError("The dedicated runtime must match XGBoost 3.4.1")
    integrity = json.loads((destination / "integrity.json").read_text(encoding="utf-8"))
    for relative, expected_hash in integrity["files"].items():
        if digest(destination / relative) != expected_hash:
            raise ValueError(f"Integrity mismatch before runtime smoke: {relative}")
    record = {
        "age_years": 45.0,
        "bmi_kg_m2": 24.0,
        "sex_female": 1.0,
        "blood_lead_ug_dl": 1.0,
        "blood_cadmium_ug_l": 0.3,
        "blood_total_mercury_ug_l": 0.7,
    }
    results = []
    for card_path in sorted(destination.glob("*/*/MODEL_CARD.json")):
        card = json.loads(card_path.read_text(encoding="utf-8"))
        values = []
        for component in card["components"]:
            features = component["features"]
            frame = pd.DataFrame([[record.get(name, np.nan) for name in features]], columns=features, dtype=float)
            config = component["config"]
            model_path = card_path.parent / Path(component["model_file"]).name
            if config["family"] == "xgboost":
                model = xgb.Booster(params={"nthread": 4, "device": "cpu"})
                model.load_model(model_path)
                model.set_param({"nthread": 4, "device": "cpu"})
                if model.feature_names != features:
                    raise ValueError(f"Feature order mismatch: {model_path}")
                estimate = float(model.predict(xgb.DMatrix(frame, nthread=4))[0])
            elif config["family"] == "catboost":
                model = CatBoostRegressor()
                model.load_model(str(model_path))
                if model.feature_names_ != features:
                    raise ValueError(f"Feature order mismatch: {model_path}")
                estimate = float(model.predict(frame, thread_count=4)[0])
            else:
                raise ValueError("Unknown released learner family")
            if config["target_transform"] == "log1p":
                estimate = math.expm1(estimate)
            elif config["target_transform"] != "identity":
                raise ValueError("Unknown released label transform")
            if not math.isfinite(estimate):
                raise ValueError(f"Nonfinite saved-model prediction: {model_path}")
            values.append(estimate * component["weight"])
        results.append({"target": card["target"], "profile": card["profile"], "finite": math.isfinite(sum(values)), "components": len(values)})
    if len(results) != 24:
        raise ValueError("Expected all 24 saved model profiles")
    versions = {name: importlib.metadata.version(name) for name in ("fastapi", "pydantic", "numpy", "pandas", "scipy", "scikit-learn", "xgboost", "catboost", "threadpoolctl")}
    report = {
        "run_id": RUN_ID,
        "synthetic_inputs_only": True,
        "training_or_test_csv_read": False,
        "fit_calls": 0,
        "all_24_saved_models_loaded_and_predicted": True,
        "native_threads_requested": 4,
        "versions": versions,
        "results": results,
    }
    same_or_create(destination / "LOCAL_RUNTIME_SMOKE.json", (json.dumps(report, indent=2, ensure_ascii=False) + "\n").encode("utf-8"))
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--smoke", action="store_true", help="Check all 24 saved models after the hash-verified copy")
    args = parser.parse_args()
    print(json.dumps(prepare(args.source, PROJECT / "models" / "nhanes_v5"), indent=2, ensure_ascii=False))
    if args.smoke:
        print(json.dumps(smoke(PROJECT / "models" / "nhanes_v5"), indent=2, ensure_ascii=False))
