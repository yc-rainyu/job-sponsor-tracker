import re
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
    'skilled worker',
    'graduate visa',
    'relocation',
)
_DECLINE = (
    'unable',
    'cannot',
    'not able',
    'no sponsorship',
    'without sponsorship',
    'do not offer',
)
_RTW = ('must have', 'must already have', 'must be eligible to work', 'right to work')
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


def split_sentences(text):
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


def _contains(sentence, phrases):
    lower = sentence.lower()
    return any(phrase in lower for phrase in phrases)


def _label(sentence):
    if _contains(sentence, _DECLINE) or _NO_SPONSOR.search(sentence):
        return 'declines'
    if _contains(sentence, _RTW):
        return 'requires_rtw'
    if _contains(sentence, _OFFER):
        return 'offers'
    return 'mentions'


def detect_visa(text):
    hits = []
    for sentence in split_sentences(text):
        if not _contains(sentence, _VISA_WORDS):
            continue
        hits.append({'text': sentence, 'label': _label(sentence)})
    if not hits:
        return {'verdict': 'none', 'sentences': []}
    for verdict in ('declines', 'requires_rtw', 'offers', 'mentions'):
        if any(hit['label'] == verdict for hit in hits):
            return {'verdict': verdict, 'sentences': hits}


# Salary
_SALARY_RE = re.compile(
    r'(up to\s+)?'
    r'(£|€|GBP|NT\$|TWD)\s*'
    r'(\d{1,3}(?:,\d{3})+|\d+)'
    r'(k)?'
    r'(?:\s*(?:[-–]|to)\s*(?:£|€|GBP|NT\$|TWD)?\s*'
    r'(\d{1,3}(?:,\d{3})+|\d+)'
    r'(k)?)?'
    r'(?:\s*(per annum|pa|per day|per hour|a year))?',
    re.IGNORECASE,
)
_CURRENCY = {'£': 'GBP', '€': 'EUR', 'gbp': 'GBP', 'nt$': 'TWD', 'twd': 'TWD'}
_PERIOD = {
    'per annum': 'year',
    'pa': 'year',
    'a year': 'year',
    'per day': 'day',
    'per hour': 'hour',
}


def _amount(num, thousands):
    value = int(num.replace(',', ''))
    if thousands:
        value *= 1000
    return value


def extract_salary(text):
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


def extract_work_mode(text):
    match = _WORK_MODE_RE.search(text)
    if not match:
        return None
    return _WORK_MODE[match.group(0).lower()]


# Years of experience
_EXPERIENCE_RE = re.compile(
    r'(\d+)\+?\s*(?:-|to|–)?\s*(\d+)?\s*years?',
    re.I,
)


def extract_experience(text):
    for match in _EXPERIENCE_RE.finditer(text):
        start, end = match.span()
        window = text[max(0, start - 30) : min(len(text), end + 30)]
        if 'experience' not in window.lower():
            continue
        years_min = int(match.group(1))
        years_max = int(match.group(2)) if match.group(2) else None
        return {'min': years_min, 'max': years_max, 'raw': match.group(0)}
    return None


# Skills
_REQUIRED_HEAD = re.compile(
    r'^(requirements|must have|essential|what you.?ll need)\s*$',
    re.I,
)
_NICE_HEAD = re.compile(
    r'^(nice to have|desirable|bonus(?: points)?|preferred|plus)\s*$',
    re.I,
)


def _longest(skill):
    names = [skill['name'], *skill['aliases']]
    return max(len(name) for name in names)


def load_skills():
    with SKILLS_PATH.open() as skills_file:
        skills = yaml.safe_load(skills_file)
    skills.sort(key=_longest, reverse=True)
    return skills


def _split_skill_sections(text):
    sections = []
    bucket = 'mentioned'
    buf = []

    def flush():
        if buf:
            sections.append((bucket, '\n'.join(buf)))
            buf.clear()

    for line in text.splitlines():
        stripped = line.strip()
        if _REQUIRED_HEAD.match(stripped):
            flush()
            bucket = 'required'
            continue
        if _NICE_HEAD.match(stripped):
            flush()
            bucket = 'nice_to_have'
            continue
        buf.append(line)
    flush()
    return sections


def _skill_in(chunk, terms):
    for term in terms:
        pattern = re.compile(rf'(?<![\w.]){re.escape(term)}(?!\w)', re.I)
        if pattern.search(chunk):
            return True
    return False


def extract_skills(text):
    rank = {'required': 3, 'nice_to_have': 2, 'mentioned': 1}
    found = {}
    sections = _split_skill_sections(text)
    for skill in load_skills():
        terms = [skill['name'], *skill['aliases']]
        for bucket, chunk in sections:
            if not _skill_in(chunk, terms):
                continue
            name = skill['name']
            if name not in found or rank[bucket] > rank[found[name]]:
                found[name] = bucket
    result = {'required': [], 'nice_to_have': [], 'mentioned': []}
    for name, bucket in found.items():
        result[bucket].append(name)
    return result


def analyse(text):
    return {
        'visa': detect_visa(text),
        'salary': extract_salary(text),
        'work_mode': extract_work_mode(text),
        'experience_years': extract_experience(text),
        'skills': extract_skills(text),
    }
