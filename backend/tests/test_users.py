import pytest
from django.contrib.auth import get_user_model


@pytest.mark.django_db
def test_passwords_are_hashed_with_argon2() -> None:
    user = get_user_model().objects.create_user(username="reader", password="s3cure-Passw0rd!")

    assert user.password.startswith("argon2$")
    assert user.check_password("s3cure-Passw0rd!")
