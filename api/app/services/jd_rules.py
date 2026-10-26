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
    'authorized to work',
    'authorised to work',
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


def _heading_key(line):
    text = line.strip()
    text = text.replace('\u2019', "'").replace('\u2018', "'")
    text = re.sub(r'^#+\s*', '', text)
    text = text.strip('*').strip()
    text = text.rstrip(':').strip()
    return re.sub(r'\s+', ' ', text)


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
        heading = _heading_key(line)
        if _REQUIRED_HEAD.match(heading):
            flush()
            bucket = 'required'
            continue
        if _NICE_HEAD.match(heading):
            flush()
            bucket = 'nice_to_have'
            continue
        buf.append(line)
    flush()
    return sections


def _term_spans(chunk, terms, name_case_sensitive):
    spans = []
    for index, term in enumerate(terms):
        ignore_case = not (name_case_sensitive and index == 0)
        flags = re.I if ignore_case else 0
        pattern = re.compile(rf'(?<![\w.]){re.escape(term)}(?!\w)', flags)
        spans.extend(match.span() for match in pattern.finditer(chunk))
    return spans


def _first_free_span(spans, occupied):
    for span in spans:
        if any(span[0] < end and start < span[1] for start, end in occupied):
            continue
        return span
    return None


def extract_skills(text):
    rank = {'required': 3, 'nice_to_have': 2, 'mentioned': 1}
    found = {}
    sections = _split_skill_sections(text)
    occupied = [[] for _ in sections]
    for skill in load_skills():
        terms = [skill['name'], *skill['aliases']]
        name_case_sensitive = bool(skill.get('case_sensitive'))
        for index, (bucket, chunk) in enumerate(sections):
            spans = _term_spans(chunk, terms, name_case_sensitive)
            span = _first_free_span(spans, occupied[index])
            if span is None:
                continue
            occupied[index].extend(spans)
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
