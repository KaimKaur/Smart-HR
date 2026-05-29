from app.core.security import hash_password, verify_password


def test_hash_password_uses_argon2() -> None:
    hashed = hash_password("SecurePass123!")
    assert hashed.startswith("$argon2")


def test_verify_password_correct() -> None:
    hashed = hash_password("SecurePass123!")
    assert verify_password("SecurePass123!", hashed) is True


def test_verify_password_incorrect() -> None:
    hashed = hash_password("SecurePass123!")
    assert verify_password("WrongPassword!", hashed) is False
