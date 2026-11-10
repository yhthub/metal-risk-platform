import asyncio
import json
import re

from fastapi import HTTPException
from app.api import plan
from app.models.prediction_schemas import PredictionPerson
from app.utils.participant_ids import participant_id


def test_plan_references_stay_consistent_across_public_outputs():
    plans = asyncio.run(plan.list_all_plans(None))
    comparisons = asyncio.run(plan.get_intervention_comparison())
    assert len({p.person_id for p in plans}) == len(plans) == 10
    assert all(p.model_dump()['name'] == p.person_id for p in plans)
    assert all(row['name'] == row['person_id'] for row in comparisons)
    for item in plans:
        report = asyncio.run(plan.generate_person_report(item.person_id))
        assert report['name'] == report['person_id'] == item.person_id
        assert report['report_title'] == f'{item.person_id} · 干预方案报告'
        assert report['reviewer'] is None


def test_free_text_is_not_a_display_identifier():
    inputs = dict(age=45, gender='male', gender_confirmed=True, bmi=24.0, pb=1.0, cd=0.4, hg=0.6)
    for value in ['0013', 'SZ-105', 'P-000000001234', 'DEMO-CLEAN-001']:
        assert PredictionPerson(id=value, **inputs).id == value
    private = '测试人员-123'
    result = PredictionPerson(id=private, **inputs)
    assert re.fullmatch(r'P-[0-9]{12}', result.id)
    assert private not in result.model_dump_json()
    assert re.fullmatch(r'P-[0-9]{12}', participant_id(''))
    try:
        asyncio.run(plan.generate_person_report(private))
    except HTTPException as exc:
        assert exc.status_code == 404 and private not in json.dumps(exc.detail, ensure_ascii=False)
    else:
        raise AssertionError('Unexpected record for unknown participant')
