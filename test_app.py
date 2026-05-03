import pytest
import os
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import app
import db


@pytest.fixture
def client():
    original_db_path = db.DB_PATH
    db.DB_PATH = tempfile.mktemp()
    db.init_db()
    app.app.config['TESTING'] = True
    app.app.config['SECRET_KEY'] = 'test-key'
    with app.app.test_client() as client:
        with app.app.test_request_context():
            yield client
    os.unlink(db.DB_PATH)
    db.DB_PATH = original_db_path


def test_index_empty(client):
    response = client.get('/')
    assert response.status_code == 200
    assert b'To Do' in response.data


def test_create_task(client):
    client.post('/task', data={'title': 'Test task', 'description': 'Test desc'})
    response = client.get('/')
    assert b'Test task' in response.data


def test_create_task_with_new_tag(client):
    client.post('/task', data={
        'title': 'Tagged',
        'description': '',
        'tag_text': ['ВАЖНО'],
        'tag_color': ['#e74c3c']
    })
    response = client.get('/')
    assert b'важно' in response.data


def test_tag_case_insensitive_preset(client):
    client.post('/task', data={
        'title': 'First',
        'tag_text': ['Работа'],
        'tag_color': ['#3498db']
    })
    presets = db.get_all_tag_presets()
    texts = [p['text'] for p in presets]
    assert 'работа' in texts
    assert 'Работа' not in texts


def test_same_text_different_color_creates_new_preset(client):
    client.post('/task', data={
        'title': 'A',
        'tag_text': ['тест'],
        'tag_color': ['#e74c3c']
    })
    client.post('/task', data={
        'title': 'B',
        'tag_text': ['тест'],
        'tag_color': ['#3498db']
    })
    presets = db.get_all_tag_presets()
    matching = [p for p in presets if p['text'] == 'тест']
    assert len(matching) == 2
    colors = {p['color'] for p in matching}
    assert '#e74c3c' in colors
    assert '#3498db' in colors


def test_limit_decrease_removes_most_recent(client):
    for i in range(5):
        client.post('/task', data={'title': f'Task {i}'})
    order_of_moving = []
    for i in range(5):
        client.post(f'/task/{i+1}/move', data={'status': 'in_progress', 'limit': '10'})
        order_of_moving.append(i + 1)
    client.post('/set-limit', data={'limit': '2'})
    in_progress = [t for t in db.get_all_tasks() if t['status'] == 'in_progress']
    in_progress_ids = {t['id'] for t in in_progress}
    assert len(in_progress_ids) == 2
    assert 1 in in_progress_ids
    assert 2 in in_progress_ids
    assert 5 not in in_progress_ids


def test_delete_task(client):
    client.post('/task', data={'title': 'Delete me'})
    client.post('/task/1/delete')
    assert b'Delete me' not in client.get('/').data


def test_toggle_desc_button_present(client):
    client.post('/task', data={'title': 'Desc', 'description': 'Text'})
    assert b'toggle-desc' in client.get('/').data