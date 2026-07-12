import pytest
from app import app, db, User
from werkzeug.security import generate_password_hash

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    with app.app_context():
        db.drop_all()
        db.create_all()
        admin = User(
            nama='Admin Test',
            email='admin@test.com',
            password=generate_password_hash('admin123'),
            role='Admin',
        )
        db.session.add(admin)
        db.session.commit()
        yield app.test_client()
        db.session.remove()
        db.drop_all()


def test_surat_api_returns_empty_list(client):
    with client.session_transaction() as sess:
        sess['_user_id'] = '1'
        sess['_fresh'] = True
    resp = client.get('/api/surat')
    assert resp.status_code == 200
    assert resp.get_json() == []


def test_upload_pdf_requires_file(client):
    with client.session_transaction() as sess:
        sess['_user_id'] = '1'
        sess['_fresh'] = True
    resp = client.post('/api/surat/upload-pdf')
    assert resp.status_code == 400
