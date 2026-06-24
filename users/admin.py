from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import Group
from .models import User


# Убираем вкладку Groups из админки
admin.site.unregister(Group)


class CustomUserAdmin(UserAdmin):
    model = User
    
    # Поля в списке пользователей
    list_display = ('email', 'name', 'surname', 'is_active', 'is_staff', 'is_superuser')
    list_filter = ('is_active', 'is_staff', 'is_superuser')
    search_fields = ('email', 'name', 'surname')
    ordering = ('email',)
    
    # Поля при редактировании пользователя
    fieldsets = (
        ('Данные для входа', {'fields': ('email', 'password')}),
        ('Личная информация', {'fields': ('name', 'surname', 'avatar', 'about', 'phone', 'github_url')}),
        ('Разрешения', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Важные даты', {'fields': ('last_login',)}),
    )
    
    # Поля при создании нового пользователя
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'name', 'surname', 'password1', 'password2'),
        }),
    )


admin.site.register(User, CustomUserAdmin)
