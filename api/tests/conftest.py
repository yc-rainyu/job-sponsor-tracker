import os
from datetime import date
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

# CI sets DATABASE_URL, local runs read it from the root .env
_env_file = Path(__file__).resolve().parents[2] / '.env'
if 'DATABASE_URL' not in os.environ and _env_file.is_file():
    for _line in _env_file.read_text().splitlines():
        _key, _equals, _value = _line.strip().partition('=')
        if _equals and not _key.startswith('#'):
            os.environ.setdefault(_key, _value)

# same server, test database, set before app code creates the engine
os.environ['DATABASE_URL'] = os.environ['DATABASE_URL'].rsplit('/', 1)[0] + '/jst_test'
os.environ['APP_ENV'] = 'test'

from app.core.deps import get_db  # noqa: E402
from app.core.rate_limit import reset  # noqa: E402
from app.db.engine import engine  # noqa: E402
from app.main import app  # noqa: E402
from app.services.sponsors.import_aliases import import_aliases  # noqa: E402
from app.services.sponsors.import_register import import_register  # noqa: E402

REGISTER_HEADER = 'Organisation Name,Town/City,County,Type & Rating,Route'
SEED_REGISTER = [
    # trading name, plus the official names behind the aliases
    'Roofoods Ltd t/a Deliveroo,London,,Worker (A rating),Skilled Worker',
    'Roofoods Ltd t/a Deliveroo,London,,Worker (A rating),Intra-Company Routes',
    'Eui Limited,Cardiff,,Worker (A rating),Skilled Worker',
    'ESSO Petroleum Company Ltd,Leatherhead,Surrey,Worker (A rating),Skilled Worker',
    # several J.P. Morgans, Stripe is not an exact legal name
    'J.P. Morgan Securities plc,London,,Worker (A rating),Skilled Worker',
    'J.P. Morgan Europe Limited,London,,Worker (A rating),Skilled Worker',
    'J.P. Morgan Chase Bank N.A.,Bournemouth,,Worker (A rating),Skilled Worker',
    'Stripe Payments UK Ltd,London,,Worker (A rating),Skilled Worker',
    # same name in two towns, then filler so junk queries stay empty
    'Same Name Ltd,London,,Worker (A rating),Skilled Worker',
    'Same Name Ltd,Manchester,,Worker (A rating),Skilled Worker',
    'Marks & Spencer PLC,London,,Worker (A rating),Skilled Worker',
    'AaruvikA Limited,Edinburgh,,Worker (A rating),Skilled Worker',
    'Solo Trader Ltd,,,Worker (A rating),Skilled Worker',
    'Another Corp Ltd,Bristol,,Worker (A rating),Skilled Worker',
    'Widget Co Ltd,Birmingham,,Worker (A rating),Skilled Worker',
    'Acme Limited,Glasgow,,Worker (A rating),Skilled Worker',
    # no Skilled Worker, and a B rating
    'Creative Only Ltd,London,,Temporary Worker (A rating),Creative Worker',
    'B Rating Ltd,Leeds,,Worker (B rating),Skilled Worker',
    # B on one route only, and an A (Premium) licence
    'Mixed Licence Ltd,Slough,,Worker (B rating),Skilled Worker',
    'Mixed Licence Ltd,Slough,,Temporary Worker (A rating),Creative Worker',
    'Premium Rated Ltd,London,,Worker (A (Premium)),Skilled Worker',
    # word match on "roofoods" that would sort before the exact one by town
    'Roofoods Holdings Ltd,Bath,,Worker (A rating),Skilled Worker',
]
SEED_ALIASES = [
    'Admiral,Eui Limited,Cardiff',
    'ExxonMobil,ESSO Petroleum Company Ltd,Leatherhead',
]


@pytest.fixture
def client(session):
    def _get_db():
        yield session

    app.dependency_overrides[get_db] = _get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def session():
    with engine.connect() as connection:
        transaction = connection.begin()
        session = Session(connection)
        yield session
        session.close()
        transaction.rollback()


@pytest.fixture
def seed_sponsors(session, tmp_path):
    def seed(extra_rows=()):
        register_csv = tmp_path / 'register.csv'
        register_csv.write_text(
            '\n'.join([REGISTER_HEADER, *SEED_REGISTER, *extra_rows]) + '\n'
        )
        aliases_csv = tmp_path / 'aliases.csv'
        aliases_csv.write_text('\n'.join(['alias,name,town', *SEED_ALIASES]) + '\n')
        import_register(session, register_csv, date(2026, 10, 16))
        import_aliases(session, aliases_csv)

    return seed


@pytest.fixture(autouse=True)
def _clear_rate_limit():
    reset()
