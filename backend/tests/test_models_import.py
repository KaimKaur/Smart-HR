def test_all_models_import_and_register_metadata() -> None:
    from app.core.database import Base
    from app.database import models

    assert len(models.__all__) == 35
    assert len(Base.metadata.tables) == 35
    assert "users" in Base.metadata.tables
    assert "audit_logs" in Base.metadata.tables
