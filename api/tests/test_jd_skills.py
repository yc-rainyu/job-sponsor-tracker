from app.services.jd_rules import load_skills


def test_postgres_alias():
    by_name = {skill['name']: skill for skill in load_skills()}
    assert 'postgres' in by_name['PostgreSQL']['aliases']


def test_nextjs_alias():
    by_name = {skill['name']: skill for skill in load_skills()}
    assert 'nextjs' in by_name['Next.js']['aliases']


def test_sql_server_before_sql():
    names = [skill['name'] for skill in load_skills()]
    assert names.index('SQL Server') < names.index('SQL')
