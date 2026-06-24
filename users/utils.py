import io
import random

from PIL import Image, ImageDraw, ImageFont
from django.core.files.base import ContentFile
from django.core.paginator import Paginator

AVATAR_SIZE = (200, 200)
AVATAR_FONT_SIZE = 100
AVATAR_FONT_PATH = "static/fonts/Neue_Haas_Grotesk_Display_Pro_75_Bold.otf"
AVATAR_TEXT_POSITION = (100, 100)
AVATAR_TEXT_FILL = "white"
AVATAR_FORMAT = "PNG"

AVATAR_COLORS = [
    (52, 152, 219),  # синий
    (46, 204, 113),  # зелёный
    (155, 89, 182),  # фиолетовый
    (241, 196, 15),  # жёлтый
    (230, 126, 34),  # оранжевый
    (231, 76, 60),  # красный
]


def generate_avatar(instance):
    if instance.avatar:
        return
    letter = instance.name[0].upper() if instance.name else "U"
    bg_color = random.choice(AVATAR_COLORS)
    img = Image.new("RGB", AVATAR_SIZE, color=bg_color)
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype(AVATAR_FONT_PATH, AVATAR_FONT_SIZE)
    except Exception:
        font = ImageFont.load_default()
    draw.text(
        AVATAR_TEXT_POSITION, letter, fill=AVATAR_TEXT_FILL, anchor="mm", font=font
    )
    buf = io.BytesIO()
    img.save(buf, format=AVATAR_FORMAT)
    instance.avatar.save(
        f"avatar_{instance.pk}.png", ContentFile(buf.getvalue()), save=False
    )


def get_paginator(queryset, request, per_page):
    paginator = Paginator(queryset, per_page)
    page_number = request.GET.get("page")
    return paginator.get_page(page_number)
