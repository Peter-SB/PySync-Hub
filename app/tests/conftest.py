import pytest
from unittest.mock import MagicMock
from app import create_app, extensions
from config import TestConfig
from app.services.spotify_service import SpotifyService


@pytest.fixture(scope="session")
def app():
    """Create and configure a new app instance for tests."""
    app = create_app(TestConfig)  # Create the app normally

    with app.app_context():
        db.create_all()

    yield app  # Provide the app instance to tests

    with app.app_context():
        db.drop_all()


@pytest.fixture(scope="function")
def db_session(app):
    """Provides a function-scoped database session."""
    with app.app_context():
        db.session.begin_nested()
        yield db
        db.session.rollback()


@pytest.fixture(scope="function")
def client(app):
    """Returns a test client for making requests."""
    return app.test_client()
