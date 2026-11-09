import datetime
import hashlib
import logging
import re
import uuid
from functools import cache
from pathlib import Path

import anthropic
from fastapi import HTTPException
from pydantic import ValidationError
from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.core.settings import settings
from app.models.ai import AiUsage, JdAnalysis
from app.models.user import User
from app.schemas.jd import AiExtraction, AiVisa
from app.services.jd_rules import analyse, pick_verdict

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = Path(__file__).with_name('jd_ai_prompt.txt').read_text()
# the API takes JSON Schema; this also moves limits it can't enforce into descriptions
OUTPUT_SCHEMA = anthropic.transform_schema(AiExtraction)
NOT_A_JOB_DESCRIPTION = (
    "This doesn't look like a job description. Paste the job posting and try again."
)
_TAG = re.compile(r'</?\s*job_description\s*>', re.I)


class _Fallback(Exception):
    pass


@cache
def _client() -> anthropic.Anthropic:
    return anthropic.Anthropic(
        api_key=settings.anthropic_api_key, timeout=30, max_retries=1
    )


def analyse_with_ai(session: Session, user: User, text: str) -> dict:
    if user.is_demo:
        raise HTTPException(
            status_code=403,
            detail='AI analysis is not available in the demo. '
            'Sign in with Google to use it.',
        )
    if not settings.ai_enabled or not settings.anthropic_api_key:
        return _rules(text, 'ai_off')

    model = settings.ai_model
    # pasting the same posting again often changes only the whitespace
    digest = hashlib.sha256(_normalise(text).encode()).hexdigest()
    cached = session.scalar(
        select(JdAnalysis.result).where(
            JdAnalysis.text_sha256 == digest, JdAnalysis.model == model
        )
    )
    if cached is not None:
        return _answer(AiExtraction.model_validate(cached))

    today = datetime.datetime.now(datetime.UTC).date()
    if _used_today(session, today) >= settings.ai_daily_total:
        return _rules(text, 'ai_off')
    if not _reserve(session, user.id, today):
        return _rules(text, 'limit_reached')

    posting = _TAG.sub('', text)
    try:
        extraction, input_tokens, output_tokens = _extract(posting, model)
        if extraction.is_job_description:
            extraction.visa = _keep_found_quotes(extraction.visa, posting, model)
    except _Fallback as reason:
        logger.warning('AI analysis fell back to rules (%s): %s', model, reason)
        return _rules(text, 'ai_failed')

    session.execute(
        insert(JdAnalysis)
        .values(
            text_sha256=digest,
            model=model,
            result=extraction.model_dump(mode='json'),
            input_tokens=input_tokens,
            output_tokens=output_tokens,
        )
        .on_conflict_do_nothing(index_elements=['text_sha256', 'model'])
    )
    session.commit()
    return _answer(extraction)


def _rules(text: str, notice: str) -> dict:
    return {**analyse(text), 'mode': 'rules', 'notice': notice}


def _answer(extraction: AiExtraction) -> dict:
    if not extraction.is_job_description:
        raise HTTPException(status_code=422, detail=NOT_A_JOB_DESCRIPTION)
    result = extraction.model_dump(exclude={'is_job_description'})
    return {**result, 'mode': 'ai', 'notice': None}


def _used_today(session: Session, today: datetime.date) -> int:
    return session.scalar(
        select(func.coalesce(func.sum(AiUsage.count), 0)).where(
            AiUsage.used_on == today
        )
    )


def _reserve(session: Session, user_id: uuid.UUID, today: datetime.date) -> bool:
    # one statement, so two requests at once can't both take the last one
    count = session.scalar(
        insert(AiUsage)
        .values(user_id=user_id, used_on=today, count=1)
        .on_conflict_do_update(
            index_elements=['user_id', 'used_on'],
            set_={'count': AiUsage.count + 1},
            where=AiUsage.count < settings.ai_daily_limit,
        )
        .returning(AiUsage.count)
    )
    session.commit()
    return count is not None


def _extract(posting: str, model: str) -> tuple[AiExtraction, int, int]:
    try:
        response = _client().messages.create(
            model=model,
            max_tokens=4000,
            system=[
                {
                    'type': 'text',
                    'text': SYSTEM_PROMPT,
                    'cache_control': {'type': 'ephemeral'},
                }
            ],
            messages=[
                {
                    'role': 'user',
                    'content': f'<job_description>\n{posting}\n</job_description>',
                }
            ],
            output_config={
                'effort': 'low',
                'format': {'type': 'json_schema', 'schema': OUTPUT_SCHEMA},
            },
        )
    except anthropic.AnthropicError as error:
        # the class name says what failed; the message can echo the request
        raise _Fallback(type(error).__name__) from None

    if response.stop_reason != 'end_turn':
        raise _Fallback(f'stop_reason {response.stop_reason}')
    raw = ''.join(block.text for block in response.content if block.type == 'text')
    try:
        extraction = AiExtraction.model_validate_json(raw)
    except ValidationError as error:
        # the count only: the errors quote the output
        raise _Fallback(f'invalid output, {error.error_count()} errors') from None

    usage = response.usage
    input_tokens = (
        usage.input_tokens
        + (usage.cache_creation_input_tokens or 0)
        + (usage.cache_read_input_tokens or 0)
    )
    return extraction, input_tokens, usage.output_tokens


def _normalise(text: str) -> str:
    return ' '.join(text.split())


def _keep_found_quotes(visa: AiVisa, posting: str, model: str) -> AiVisa:
    haystack = _normalise(posting)
    kept = []
    for sentence in visa.sentences:
        quote = _normalise(sentence.text)
        if quote and quote in haystack:
            kept.append(sentence)

    dropped = len(visa.sentences) - len(kept)
    if dropped:
        logger.warning(
            'AI analysis dropped %d of %d visa quotes (%s)',
            dropped,
            len(visa.sentences),
            model,
        )
    if visa.sentences and not kept:
        raise _Fallback('no visa quote found in the posting')

    labels = {sentence.label for sentence in kept}
    return AiVisa(verdict=pick_verdict(labels), sentences=kept)
