import json
import logging
import re
from typing import Any

from mmpy_bot import Message, Plugin, listen_to


logger = logging.getLogger(__name__)

MESSAGE_PREFIX = "КАНДИДАТ СОГЛАСОВАН."

PHONE_RE = re.compile(r"^\+?\d[\d\s().-]{7,}\d$")

FIELD_LABELS = {
    "гражданство": "country",
    "возраст": "age",
    "срок вахты": "work_time",
    "тип занятости": "work_type",
    "статус проверки": "status",
    "менеджер": "referral",
}


def parse(text: str):
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    candidate: dict[str, Any] = {
        "name": None,
        "phone": None,
        "country": None,
        "age": None,
        "work_place": None,
        "work_position": None,
        "work_type": None,
        "work_time": None,
        "status": None,
        "referral": None,
    }

    if not lines:
        return candidate

    payload_lines = lines[1:] if lines[0].startswith(MESSAGE_PREFIX) else lines
    if payload_lines:
        candidate["name"] = payload_lines[0]

    for line in payload_lines[1:]:
        if line.upper() == "СОГЛАСОВАНО":
            continue

        if PHONE_RE.match(line):
            candidate["phone"] = line
            continue

        if ":" in line:
            label, value = line.split(":", 1)
            field_name = FIELD_LABELS.get(label.strip().lower())
            if field_name:
                candidate[field_name] = value.strip()
            continue

        if "/" in line and not candidate["work_place"] and not candidate["work_position"]:
            work_place, work_position = line.split("/", 1)
            candidate["work_place"] = work_place.strip()
            candidate["work_position"] = work_position.strip()

    if isinstance(candidate["age"], str) and candidate["age"].isdigit():
        candidate["age"] = int(candidate["age"])

    return candidate


class ParserPlugin(Plugin):
    @listen_to(r"^КАНДИДАТ СОГЛАСОВАН\.", direct_only=False)
    async def parse(self, message: Message):
        if message.is_direct_message:
            return

        candidate = parse(message.text)
        logger.info(
            "Approved candidate parsed: %s",
            json.dumps(candidate, ensure_ascii=False),
        )
