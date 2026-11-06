import datetime
import uuid
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, field_validator

from app.schemas.jd import Experience, Salary, VisaLabel

Country = Literal['UK', 'TW', 'NL', 'US', 'other']
WorkMode = Literal['onsite', 'hybrid', 'remote', 'unknown']
Channel = Literal[
    'company_site',
    'linkedin_easy_apply',
    'job_board_104',
    'job_board_cake',
    'agency',
    'email',
    'other',
]
Status = Literal[
    'draft', 'applied', 'interviewing', 'offer', 'rejected', 'withdrawn', 'no_response'
]
SponsorStatus = Literal['on_list', 'not_found', 'agency', 'not_applicable', 'unchecked']

Name = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200)
]
Short = Annotated[str, Field(max_length=500)]
Url = Annotated[str, Field(max_length=2000)]
Long = Annotated[str, Field(max_length=20000)]
SkillName = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)
]
SkillList = Annotated[list[SkillName], Field(max_length=50)]


class SponsorCheck(BaseModel):
    status: SponsorStatus
    sponsor_id: int | None = None
    registered_name: str | None = None
    town: str | None = None
    match_type: Literal['exact', 'alias', 'trading_name', 'word', 'fuzzy'] | None = None
    score: float | None = None
    has_skilled_worker: bool | None = None
    rating: Literal['A', 'B'] | None = None
    checked_at: datetime.datetime | None = None
    register_published_on: datetime.date | None = None


# separate from the analyse result's Skills: two groups, user-edited and bounded
class ApplicationSkills(BaseModel):
    required: SkillList = []
    nice_to_have: SkillList = []


# what the rules found when the user saved from the analyse page; skills live apart
class Analysis(BaseModel):
    visa: VisaLabel | Literal['none']
    salary: Salary | None = None
    work_mode: Literal['remote', 'hybrid', 'onsite'] | None = None
    experience_years: Experience | None = None


class ApplicationCreate(BaseModel):
    company: Name
    role: Name
    country: Country
    applied_on: datetime.date | None = None
    is_approx: bool = False
    location: Short | None = None
    work_mode: WorkMode = 'unknown'
    channel: Channel = 'other'
    status: Status = 'applied'
    salary_stated: Short | None = None
    cover_letter: Long = ''
    notes: Long | None = None
    job_url: Url | None = None
    jd_text: Long | None = None
    next_step: Short | None = None
    next_step_at: datetime.datetime | None = None
    sponsor_check: SponsorCheck = Field(
        default_factory=lambda: SponsorCheck(status='unchecked')
    )
    skills: ApplicationSkills = Field(default_factory=ApplicationSkills)
    analysis: Analysis | None = None


class ApplicationUpdate(BaseModel):
    company: Name | None = None
    role: Name | None = None
    country: Country | None = None
    applied_on: datetime.date | None = None
    is_approx: bool | None = None
    location: Short | None = None
    work_mode: WorkMode | None = None
    channel: Channel | None = None
    status: Status | None = None
    salary_stated: Short | None = None
    cover_letter: Long | None = None
    notes: Long | None = None
    job_url: Url | None = None
    jd_text: Long | None = None
    next_step: Short | None = None
    next_step_at: datetime.datetime | None = None
    sponsor_check: SponsorCheck | None = None
    skills: ApplicationSkills | None = None
    analysis: Analysis | None = None

    # these columns are NOT NULL; a field left out is fine, an explicit null is not
    @field_validator(
        'company',
        'role',
        'country',
        'is_approx',
        'work_mode',
        'channel',
        'status',
        'cover_letter',
        'sponsor_check',
        'skills',
    )
    @classmethod
    def _reject_null(cls, value):
        if value is None:
            raise ValueError('cannot be null')
        return value


class Application(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    applied_on: datetime.date | None
    is_approx: bool
    country: Country
    company: str
    role: str
    location: str | None
    work_mode: WorkMode
    channel: Channel
    status: Status
    status_changed_at: datetime.datetime
    salary_stated: str | None
    cover_letter: str
    notes: str | None
    job_url: str | None
    jd_text: str | None
    next_step: str | None
    next_step_at: datetime.datetime | None
    sponsor_check: SponsorCheck
    skills: ApplicationSkills
    analysis: Analysis | None
    created_at: datetime.datetime
    updated_at: datetime.datetime
