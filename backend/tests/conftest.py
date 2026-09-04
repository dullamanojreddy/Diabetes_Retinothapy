import pytest
from app.ml.model import model_manager

@pytest.fixture(scope="session", autouse=True)
def initialize_model_for_tests():
    if not model_manager.is_loaded:
        model_manager.load_model()
    yield
