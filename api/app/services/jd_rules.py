import re
from functools import cache
from pathlib import Path

import yaml

SKILLS_PATH = Path(__file__).resolve().parents[3] / 'data' / 'skills.yaml'


# Visa
_VISA_WORDS = (
    'sponsor',
    'sponsorship',
    'visa',
    'right to work',
    'rtw',
    'work permit',
    'work authorisation',
    'work authorization',
    'settled status',
    'pre-settled',
    'ilr',
    'indefinite leave',
    'british citizen',
    'uk citizen',
    'eu citizen',
    'security clearance',
    'sc clearance',
    'dv clearance',
    'eligible to work in the uk',
    'eligibility to work',
    'authorized to work',
    'authorised to work',
    'skilled worker',
    'graduate visa',
    'relocation',
)
# only at the start of a word, so "advisable" has no visa but "sponsors" still counts
_VISA_WORD_RE = re.compile(
    r'(?<!\w)(?:' + '|'.join(re.escape(word) for word in _VISA_WORDS) + ')',
    re.I,
)
_DECLINE = (
    'unable',
    'cannot',
    'not able',
    'no sponsorship',
    'without sponsorship',
    'do not offer',
)
_RTW = (
    'must have',
    'must already have',
    'must be eligible to work',
    'right to work',
    'authorized to work',
    'authorised to work',
)
_OFFER = (
    'sponsorship available',
    'we can sponsor',
    'we are able to sponsor',
    'visa sponsorship offered',
    'open to sponsoring',
)
_NO_SPONSOR = re.compile(
    r'\b(?:no|not)\b.*\bsponsorship\b|\bsponsorship\b.*\b(?:no|not)\b',
    re.I,
)
_VERDICT_ORDER = ('declines', 'requires_rtw', 'offers', 'mentions')


def split_sentences(text: str) -> list[str]:
    sentences = []
    for line in text.splitlines():
        line = line.strip()
        line = re.sub(r'^[-*]\s*', '', line)
        if not line:
            continue
        for part in re.split(r'(?<=[.;])\s+', line):
            part = part.strip()
            if part:
                sentences.append(part)
    return sentences


def _contains(sentence: str, phrases: tuple[str, ...]) -> bool:
    lower = sentence.lower()
    return any(phrase in lower for phrase in phrases)


def _label(sentence: str) -> str:
    if _contains(sentence, _DECLINE) or _NO_SPONSOR.search(sentence):
        return 'declines'
    if _contains(sentence, _RTW):
        return 'requires_rtw'
    if _contains(sentence, _OFFER):
        return 'offers'
    return 'mentions'


def detect_visa(text: str) -> dict:
    hits = [
        {'text': sentence, 'label': _label(sentence)}
        for sentence in split_sentences(text)
        if _VISA_WORD_RE.search(sentence)
    ]
    labels = {hit['label'] for hit in hits}
    verdict = next((label for label in _VERDICT_ORDER if label in labels), 'none')
    return {'verdict': verdict, 'sentences': hits}


# Salary
_SALARY_RE = re.compile(
    r'(up to\s+)?'
    r'(£|€|GBP|NT\$|TWD)\s*'
    r'(\d{1,3}(?:,\d{3})+|\d+)(?!\d|\.\d)'
    r'(k)?'
    # £20m or £1.5bn is funding, not pay
    r'(?!\s*(?:m|bn|million|billion)\b)'
    r'(?:\s*(?:[-–]|to)\s*(?:£|€|GBP|NT\$|TWD)?\s*'
    r'(\d{1,3}(?:,\d{3})+|\d+)'
    r'(k)?)?'
    r'(?:\s*(?:gross\s+)?'
    r'(per annum|pa|per day|per hour|a year|per month|monthly|a month))?',
    re.IGNORECASE,
)
_CURRENCY = {'£': 'GBP', '€': 'EUR', 'gbp': 'GBP', 'nt$': 'TWD', 'twd': 'TWD'}
_PERIOD = {
    'per annum': 'year',
    'pa': 'year',
    'a year': 'year',
    'per day': 'day',
    'per hour': 'hour',
    'per month': 'month',
    'monthly': 'month',
    'a month': 'month',
}


def _amount(digits: str, thousands: bool) -> int:
    value = int(digits.replace(',', ''))
    if thousands:
        value *= 1000
    return value


def extract_salary(text: str) -> dict | None:
    match = _SALARY_RE.search(text)
    if not match:
        return None
    up_to, symbol, first, first_k, second, second_k, period_raw = match.groups()
    thousands = bool(first_k or second_k)
    low = _amount(first, thousands)
    high = _amount(second, thousands) if second else low
    salary_min = None if up_to else low
    salary_max = low if up_to else high
    period = _PERIOD.get((period_raw or '').lower())
    if period is None and ((salary_min or 0) >= 10000 or (salary_max or 0) >= 10000):
        period = 'year'
    return {
        'min': salary_min,
        'max': salary_max,
        'currency': _CURRENCY[symbol.lower()],
        'period': period,
        'raw': match.group(0).strip(),
    }


# Work mode
_WORK_MODE_RE = re.compile(
    r'fully remote|on-site|onsite|in office|hybrid|remote|遠端|混合|到班',
    re.I,
)
_WORK_MODE = {
    'fully remote': 'remote',
    'remote': 'remote',
    'hybrid': 'hybrid',
    'on-site': 'onsite',
    'onsite': 'onsite',
    'in office': 'onsite',
    '遠端': 'remote',
    '混合': 'hybrid',
    '到班': 'onsite',
}


def extract_work_mode(text: str) -> str | None:
    match = _WORK_MODE_RE.search(text)
    if not match:
        return None
    return _WORK_MODE[match.group(0).lower()]


# Years of experience
_EXPERIENCE_RE = re.compile(
    r'(\d+)\+?\s*(?:-|to|–)?\s*(\d+)?\s*years?',
    re.I,
)


def extract_experience(text: str) -> dict | None:
    for match in _EXPERIENCE_RE.finditer(text):
        start, end = match.span()
        line_start = text.rfind('\n', 0, start) + 1
        line_end = text.find('\n', end)
        if line_end == -1:
            line_end = len(text)
        line = text[line_start:line_end]
        if 'experience' not in line.lower():
            continue
        years_min = int(match.group(1))
        years_max = int(match.group(2)) if match.group(2) else None
        return {'min': years_min, 'max': years_max, 'raw': match.group(0)}
    return None


# Skills
_REQUIRED_HEAD = re.compile(
    r'^(requirements|required skills|must have(?: skills(?:/experience)?)?|'
    r'essential(?: skills)?|what you.?ll need|'
    r'what (?:we|they).?re looking for)$',
    re.I,
)
_NICE_HEAD = re.compile(
    r'^(nice to haves?|desirable(?: skills)?|bonus(?: points)?|preferred|plus|'
    r'advantageous(?: skills(?:/experience)?)?)$',
    re.I,
)
_BUCKET_RANK = {'required': 3, 'nice_to_have': 2, 'mentioned': 1}


def _heading_key(line: str) -> str:
    text = line.strip()
    text = text.replace('’', "'").replace('‘', "'")
    text = re.sub(r'^#+\s*', '', text)
    text = text.strip('*').strip()
    text = text.rstrip(':').strip()
    return re.sub(r'\s+', ' ', text)


def _longest(skill: dict) -> int:
    names = [skill['name'], *skill['aliases']]
    return max(len(name) for name in names)


# read once per process, restart the api after editing skills.yaml
@cache
def load_skills() -> list[dict]:
    with SKILLS_PATH.open() as skills_file:
        skills = yaml.safe_load(skills_file)
    skills.sort(key=_longest, reverse=True)
    return skills


@cache
def _skill_patterns() -> list[tuple[str, list[re.Pattern[str]]]]:
    patterns = []
    for skill in load_skills():
        terms = [skill['name'], *skill['aliases']]
        name_case_sensitive = bool(skill.get('case_sensitive'))
        compiled = [
            re.compile(
                rf'(?<![\w.]){re.escape(term)}(?!\w)',
                0 if name_case_sensitive and index == 0 else re.I,
            )
            for index, term in enumerate(terms)
        ]
        patterns.append((skill['name'], compiled))
    return patterns


def _split_skill_sections(text: str) -> list[tuple[str, str]]:
    sections = []
    bucket = 'mentioned'
    section_lines = []

    def flush():
        if section_lines:
            sections.append((bucket, '\n'.join(section_lines)))
            section_lines.clear()

    for line in text.splitlines():
        heading = _heading_key(line)
        if _REQUIRED_HEAD.match(heading):
            flush()
            bucket = 'required'
            continue
        if _NICE_HEAD.match(heading):
            flush()
            bucket = 'nice_to_have'
            continue
        section_lines.append(line)
    flush()
    return sections


def _first_free_span(
    spans: list[tuple[int, int]], occupied: list[tuple[int, int]]
) -> tuple[int, int] | None:
    for span in spans:
        if any(span[0] < end and start < span[1] for start, end in occupied):
            continue
        return span
    return None


def extract_skills(text: str) -> dict[str, list[str]]:
    found = {}
    sections = _split_skill_sections(text)
    occupied = [[] for _ in sections]
    for name, patterns in _skill_patterns():
        for index, (bucket, chunk) in enumerate(sections):
            spans = [
                match.span()
                for pattern in patterns
                for match in pattern.finditer(chunk)
            ]
            if _first_free_span(spans, occupied[index]) is None:
                continue
            occupied[index].extend(spans)
            if name not in found or _BUCKET_RANK[bucket] > _BUCKET_RANK[found[name]]:
                found[name] = bucket
    result = {'required': [], 'nice_to_have': [], 'mentioned': []}
    for name, bucket in found.items():
        result[bucket].append(name)
    return result


def analyse(text: str) -> dict:
    return {
        'visa': detect_visa(text),
        'salary': extract_salary(text),
        'work_mode': extract_work_mode(text),
        'experience_years': extract_experience(text),
        'skills': extract_skills(text),
    }
