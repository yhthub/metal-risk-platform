"""Participant references used by intake, predictions and reports."""
import re
import secrets
from typing import Annotated

from pydantic import BeforeValidator


_REFERENCE = re.compile(r'(?:[0-9]{1,13}|(?:P|SZ|DEMO|DEMO-SYNTHETIC|DEMO-CLEAN)-[0-9]{1,16})')


def new_participant_id() -> str:
    return f'P-{secrets.randbelow(10**12):012d}'


def participant_id(value: object) -> str:
    code = value.strip() if isinstance(value, str) else ''
    return code if _REFERENCE.fullmatch(code) else new_participant_id()


ParticipantID = Annotated[str, BeforeValidator(participant_id)]
