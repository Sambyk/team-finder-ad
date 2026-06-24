from django.urls import path

from . import views

urlpatterns = [
    path("list/", views.user_list, name="user_list"),
    path("register/", views.register, name="register"),
    path("login/", views.user_login, name="login"),
    path("logout/", views.user_logout, name="logout"),
    path("<int:pk>/", views.user_detail, name="user_detail"),
    path("<int:pk>/edit/", views.edit_profile, name="edit_profile"),
    path("<int:pk>/change-password/", views.change_password, name="change_password"),
]
