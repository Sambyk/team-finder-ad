from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.db import models
from PIL import Image, ImageDraw, ImageFont
import random
import io
from django.core.files.base import ContentFile


class UserManager(BaseUserManager):
    def create_user(self, email, name, surname, password=None, **extra_fields):
        if not email:
            raise ValueError('Email обязателен')
        email = self.normalize_email(email)
        user = self.model(email=email, name=name, surname=surname, **extra_fields)
        user.set_password(password)
        user.save()
        return user

    def create_superuser(self, email, name, surname, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, name, surname, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    name = models.CharField(max_length=124)
    surname = models.CharField(max_length=124)
    avatar = models.ImageField(upload_to='avatars/', blank=True)
    phone = models.CharField(max_length=12, blank=True, default='')
    github_url = models.URLField(blank=True)
    about = models.TextField(max_length=256, blank=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['name', 'surname']

    def __str__(self):
        return f'{self.name} {self.surname}'

    def generate_avatar(self):
        if self.avatar:
            return
        letter = self.name[0].upper() if self.name else 'U'
        bg_color = random.choice([
            (52, 152, 219), (46, 204, 113), (155, 89, 182),
            (241, 196, 15), (230, 126, 34), (231, 76, 60)
        ])
        img = Image.new('RGB', (200, 200), color=bg_color)
        draw = ImageDraw.Draw(img)
        try:
            font = ImageFont.truetype('static/fonts/Neue_Haas_Grotesk_Display_Pro_75_Bold.otf', 100)
        except Exception:
            font = ImageFont.load_default()
        draw.text((100, 100), letter, fill='white', anchor='mm', font=font)
        buf = io.BytesIO()
        img.save(buf, format='PNG')
        self.avatar.save(f'avatar_{self.pk}.png', ContentFile(buf.getvalue()), save=False)

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)
        if is_new:
            self.generate_avatar()
            super().save(update_fields=['avatar'])
