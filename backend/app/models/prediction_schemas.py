"""Explicit, specimen-aware inputs for the NHANES current-measurement models.

These contracts deliberately do not reuse IndividualData: its historical metal
units and category meanings differ from the frozen training inputs.
"""
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class PredictionInput(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, allow_inf_nan=False)


class PredictionPerson(PredictionInput):
    id: Optional[str] = Field(default=None, max_length=100)
    age: int = Field(ge=18, le=80, description="NHANES adult age, capped at 80; not an age-to-risk rule")
    gender: Literal["male", "female"]
    gender_confirmed: Literal[True]
    bmi: float = Field(gt=0)
    pb: float = Field(ge=0)
    cd: float = Field(ge=0)
    hg: float = Field(ge=0)

    @field_validator("bmi", "pb", "cd", "hg", mode="before")
    @classmethod
    def quantities_are_actual_numbers(cls, value):
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError("必须提供明确数值；空值、文本和布尔值不能作为测量值")
        return value

    @field_validator("gender_confirmed", mode="before")
    @classmethod
    def require_gender_confirmation(cls, value):
        if value is not True:
            raise ValueError("请明确核对性别，不能直接使用表单默认值")
        return value


class MeasurementMetadata(PredictionInput):
    sample: Literal["whole_blood"]
    unit: str = Field(min_length=1, max_length=20)
    analyte: Literal["lead", "cadmium", "total_mercury"]
    confirmed: Literal[True]

    @field_validator("confirmed", mode="before")
    @classmethod
    def confirmed_is_true(cls, value):
        if value is not True:
            raise ValueError("必须核对样本、单位及分析物后确认")
        return value


class BloodMeasurements(PredictionInput):
    pb: MeasurementMetadata
    cd: MeasurementMetadata
    hg: MeasurementMetadata


class PredictionCovariates(PredictionInput):
    # Unknown is null, not a manufactured __unknown dummy or an old Chinese
    # education/smoking-frequency category with a different meaning.
    education: Optional[Literal[
        "less_than_grade9", "grade9_11", "high_school_ged",
        "some_college_aa", "college_or_above",
    ]] = None
    marital: Optional[Literal[
        "married", "widowed", "divorced", "separated", "never_married", "living_with_partner",
    ]] = None
    smoking: Optional[Literal["less_than_100_lifetime", "former", "current"]] = None
    alcohol_any_past_year: Optional[bool] = None


class PersonPredictionRequest(PredictionInput):
    person: PredictionPerson
    measurements: BloodMeasurements
    covariates: PredictionCovariates = Field(default_factory=PredictionCovariates)


class BatchPredictionRequest(PredictionInput):
    file_id: str = Field(pattern=r"^FILE-[0-9a-f]{8}$")
    measurements: BloodMeasurements
    offset: int = Field(default=0, ge=0, le=100_000)
    limit: int = Field(default=300, ge=1, le=500)


class DashboardPredictionRequest(PredictionInput):
    input: PersonPredictionRequest
    target: Literal[
        "sbp", "dbp", "serum_creatinine_mg_dl", "bun_mg_dl", "uric_acid_mg_dl",
        "uacr_mg_g", "hba1c_percent", "total_cholesterol_mg_dl",
        "hdl_cholesterol_mg_dl", "alt_u_l", "ast_u_l", "ggt_u_l",
    ]


class CohortPredictionRequest(PredictionInput):
    file_id: str = Field(pattern=r"^FILE-[0-9a-f]{8}$")
    measurements: BloodMeasurements
