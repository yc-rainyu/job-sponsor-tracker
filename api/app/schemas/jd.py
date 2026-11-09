from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.sponsors import SponsorResult

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
    raw: str = Field(max_length=200)


class Experience(BaseModel):
    min: int
    max: int | None
    raw: str = Field(max_length=200)


class Skills(BaseModel):
    required: list[str]
    nice_to_have: list[str]
    mentioned: list[str]


class AnalyseResult(BaseModel):
    model_config = ConfigDict(json_schema_serialization_defaults_required=True)

    mode: Literal['rules', 'ai'] = 'rules'
    company: str | None = None
    role: str | None = None
    location: str | None = None
    visa: Visa
    salary: Salary | None
    work_mode: Literal['remote', 'hybrid', 'onsite'] | None
    experience_years: Experience | None
    skills: Skills
    company_matches: list[SponsorResult]
    notice: Literal['ai_off', 'limit_reached', 'ai_failed'] | None = None


# what Claude returns; bounded, unlike the rules result, which can be longer
AiSkill = Annotated[str, Field(max_length=60)]


class AiVisaSentence(BaseModel):
    text: str = Field(max_length=1000)
    label: VisaLabel


class AiVisa(BaseModel):
    verdict: VisaLabel | Literal['none']
    sentences: list[AiVisaSentence] = Field(max_length=10)


class AiSkills(BaseModel):
    required: list[AiSkill] = Field(max_length=40)
    nice_to_have: list[AiSkill] = Field(max_length=40)
    mentioned: list[AiSkill] = Field(max_length=40)


class AiExtraction(BaseModel):
    is_job_description: bool
    company: str | None = Field(max_length=200)
    role: str | None = Field(max_length=200)
    location: str | None = Field(max_length=200)
    visa: AiVisa
    salary: Salary | None
    work_mode: Literal['remote', 'hybrid', 'onsite'] | None
    experience_years: Experience | None
    skills: AiSkills
