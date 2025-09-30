import os
import pytest
from app import app

@pytest.fixture()
def client():
    app.config['TESTING'] = True
    with app.test_client() as c:
        with app.app_context():
            yield c


def test_login_page_loads(client):
    resp = client.get('/login')
    assert resp.status_code == 200


def test_news_summary_authenticated(client):
    # simulate login
    with client.session_transaction() as sess:
        sess['authenticated'] = True
    resp = client.get('/api/news/summary')
    assert resp.status_code == 200
    data = resp.get_json()
    assert 'total_articles' in data
