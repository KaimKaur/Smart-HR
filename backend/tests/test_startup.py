def test_app_imports_without_error() -> None:
    from app.main import app

    assert app.title == "Smart HR API"
