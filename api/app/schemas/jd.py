from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.sponsors import SponsorHit

VisaLabel = Literal['declines', 'requires_rtw', 'offers', 'mentions']


class AnalyseBody(BaseModel):
    text: str = Field(max_length=20000)
    company: str | None = Field(default=None, max_length=200)


class VisaSentence(BaseModel):
    text: str
    label: VisaLabel


class Visa(BaseModel):
    verdict: VisaLabel | Literal['none']
    sentences: list[VisaSentence]


class Salary(BaseModel):
    min: int | None
    max: int
    currency: Literal['GBP', 'EUR', 'TWD']
    period: Literal['year', 'month', 'day', 'hour'] | None
    raw: str


class Experience(BaseModel):
    min: int
    max: int | None
    raw: str


class Skills(BaseModel):
    required: list[str]
    nice_to_have: list[str]
    mentioned: list[str]


class AnalyseResult(BaseModel):
    visa: Visa
    salary: Salary | None
    work_mode: Literal['remote', 'hybrid', 'onsite'] | None
    experience_years: Experience | None
    skills: Skills
    company_matches: list[SponsorHit]
