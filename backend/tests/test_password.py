from app.services.password import hash_password, verify_password


def test_hash_password():
    password = "correct horse battery staple"
    password_hash = hash_password(password)

    assert password_hash != password
    assert password_hash.startswith("$argon2id$")


def test_verify_correct_password():
    password = "correct horse battery staple"
    password_hash = hash_password(password)

    assert verify_password(password, password_hash) is True


def test_verify_incorrect_password():
    password_hash = hash_password("correct horse battery staple")

    assert verify_password("wrong password", password_hash) is False


def test_hashes_use_unique_salts():
    password = "correct horse battery staple"
    first_hash = hash_password(password)
    second_hash = hash_password(password)

    assert first_hash != second_hash
    assert verify_password(password, first_hash) is True
    assert verify_password(password, second_hash) is True
