from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.main import docs_urls

DOC_PATHS = ('/docs', '/redoc', '/openapi.json')


def test_prod_hides_the_docs():
    client = TestClient(FastAPI(**docs_urls('prod')))
    for path in DOC_PATHS:
        assert client.get(path).status_code == 404


def test_dev_keeps_the_docs():
    client = TestClient(FastAPI(**docs_urls('dev')))
    for path in DOC_PATHS:
        assert client.get(path).status_code == 200
