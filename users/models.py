from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models

from .managers import UserManager
from .utils import generate_avatar

MAX_LENGTH_NAME = 124
MAX_LENGTH_SURNAME = 124
MAX_LENGTH_PHONE = 12
MAX_LENGTH_ABOUT = 256


class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    name = models.CharField(max_length=MAX_LENGTH_NAME)
    surname = models.CharField(max_length=MAX_LENGTH_SURNAME)
    avatar = models.ImageField(upload_to="avatars/", blank=True)
    phone = models.CharField(max_length=MAX_LENGTH_PHONE, blank=True, default="")
    github_url = models.URLField(blank=True)
    about = models.TextField(max_length=MAX_LENGTH_ABOUT, blank=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["name", "surname"]

    def __str__(self):
        return f"{self.name} {self.surname}"

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)
        if is_new:
            generate_avatar(self)
            super().save(update_fields=["avatar"])
