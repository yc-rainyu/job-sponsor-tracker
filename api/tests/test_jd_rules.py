import json
import signal
from pathlib import Path

import pytest

from app.services.jd_rules import analyse

FIXTURES = Path(__file__).parent / 'fixtures' / 'jd'

CASES = [
    '01-declines-explicit',
    '03-requires-rtw',
    '06-offers-sponsorship',
    '08-mentions-licensed-sponsor',
    '10-none-day-rate-no-headings',
]


@pytest.mark.parametrize('stem', CASES)
def test_analyse(stem):
    text = (FIXTURES / f'{stem}.txt').read_text()
    expected = json.loads((FIXTURES / 'expected' / f'{stem}.json').read_text())
    got = analyse(text)

    assert got['visa'] == expected['visa']
    assert got['salary'] == expected['salary']
    assert got['work_mode'] == expected['work_mode']
    assert got['experience_years'] == expected['experience_years']
    for bucket in ('required', 'nice_to_have', 'mentioned'):
        assert set(got['skills'][bucket]) == set(expected['skills'][bucket])


def test_no_visa_sponsorship_available():
    got = analyse('No visa sponsorship available.')
    assert got['visa']['verdict'] == 'declines'


def test_salary_range_with_to():
    got = analyse('Salary between £45,000 to £50,000 a year.')
    assert got['salary']['min'] == 45000
    assert got['salary']['max'] == 50000
    assert got['salary']['period'] == 'year'


def test_salary_per_month():
    got = analyse('€5,000 - €6,500 gross per month.')
    assert got['salary']['min'] == 5000
    assert got['salary']['max'] == 6500
    assert got['salary']['period'] == 'month'


def test_markdown_skill_headings():
    got = analyse("### What you'll need\n- Python\n### Bonus points\n- Docker\n")
    assert 'Python' in got['skills']['required']
    assert 'Docker' in got['skills']['nice_to_have']


def test_required_skills_heading():
    got = analyse('Required skills:\n- React\n- TypeScript\n')
    assert set(got['skills']['required']) == {'React', 'TypeScript'}


def test_advantageous_heading():
    got = analyse('Must have\n- Python\nAdvantageous skills/experience:\n- Docker\n')
    assert 'Python' in got['skills']['required']
    assert 'Docker' in got['skills']['nice_to_have']


def test_looking_for_heading():
    got = analyse("What they're looking for\n- TypeScript\n")
    assert 'TypeScript' in got['skills']['required']


def test_experience_on_same_line():
    got = analyse('* 3+ years of software development experience')
    assert got['experience_years']['min'] == 3


def test_go_as_verb():
    got = analyse('Building features that go beyond simple prompting.')
    assert 'Go' not in got['skills']['mentioned']


def test_rest_not_the_rest():
    got = analyse('The rest of the week is flexible and remote if you desire.')
    assert 'REST' not in got['skills']['mentioned']


def test_sql_server_not_sql():
    got = analyse('Requirements\n- SQL Server\n- also our SQL Server database\n')
    assert got['skills']['required'] == ['SQL Server']


def test_llms_plural():
    got = analyse('Hands-on experience building with LLMs.')
    assert 'LLM' in got['skills']['mentioned']


def test_tdd_phrase():
    got = analyse('We use a test-driven development approach.')
    assert 'TDD' in got['skills']['mentioned']


def test_funding_is_not_salary():
    got = analyse('We raised £20m last year. Salary £60,000 a year.')
    assert got['salary']['min'] == 60000


def test_visa_word_starts_a_word():
    got = analyse('It is advisable to apply early.')
    assert got['visa']['verdict'] == 'none'


@pytest.mark.parametrize(
    ('line', 'expected'),
    [
        ('3+ years of experience', (3, None)),
        ('3-5 years of experience', (3, 5)),
        ('3 - 5 years of experience', (3, 5)),
        ('3 to 5 years of experience', (3, 5)),
        ('2–4 years of experience', (2, 4)),
        ('10+ years of experience', (10, None)),
        ('Minimum 1 year of experience', (1, None)),
    ],
)
def test_experience_phrasings(line, expected):
    got = analyse(line)['experience_years']
    assert (got['min'], got['max']) == expected


def test_no_and_sponsorship_far_apart_still_declines():
    got = analyse('There is no budget this year for visa sponsorship.')
    assert got['visa']['verdict'] == 'declines'


HOSTILE = {
    'digits': '1' * 20000,
    'spaces after a digit': '3' + ' ' * 19998 + 'x',
    'no before sponsor': 'no ' * 6664 + 'sponsor',
}


def _too_slow(signum, frame):
    raise TimeoutError('analyse took over 0.5s, a regex is probably backtracking')


@pytest.mark.parametrize('text', HOSTILE.values(), ids=HOSTILE.keys())
def test_hostile_input_stays_fast(text):
    previous = signal.signal(signal.SIGALRM, _too_slow)
    signal.setitimer(signal.ITIMER_REAL, 0.5)
    try:
        analyse(text)
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous)
