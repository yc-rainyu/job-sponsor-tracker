import json
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
