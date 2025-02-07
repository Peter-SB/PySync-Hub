import pytest
from app import create_app, db as _db
from config import TestConfig

@pytest.fixture(scope='session')
def app():
    """
    Returns session-wide application.
    """
    app = create_app()
    app.config.from_object(TestConfig)
    with app.app_context():
        _db.create_all()

    yield app

    with app.app_context():
        _db.drop_all()

@pytest.fixture(scope='function')
def db(app):
    """
    Returns function-scoped session-wide database.
    """
    from app import db as _db
    with app.app_context():
        _db.session.begin_nested()
        yield _db
        _db.session.rollback()

@pytest.fixture(scope='function')
def client(app):
    """
    Returns a test client for the application.
    """
    return app.test_client()
