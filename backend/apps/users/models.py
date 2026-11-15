from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    """Project user model.

    Defined from day one because swapping AUTH_USER_MODEL later is painful.
    Intentionally identical to AbstractUser until real requirements exist.
    """
