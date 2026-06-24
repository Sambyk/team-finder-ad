from django import forms
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm

from .utils import get_paginator

User = get_user_model()
PHONE_LENGTH = 12
PAGINATOR_PER_PAGE = 12


# --- Форма входа (email вместо username) ---
class EmailAuthenticationForm(AuthenticationForm):
    username = forms.EmailField(
        label="Email", widget=forms.EmailInput(attrs={"autofocus": True})
    )


# --- Форма регистрации ---
class RegisterForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ["name", "surname", "email"]

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])
        if commit:
            user.save()
        return user


# --- Форма редактирования профиля ---
class EditProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["name", "surname", "avatar", "about", "phone", "github_url"]

    def clean_phone(self):
        phone = self.cleaned_data.get("phone", "")
        if not phone:
            return phone
        if phone.startswith("8"):
            phone = "+7" + phone[1:]
        if not phone.startswith("+7") or len(phone) != PHONE_LENGTH:
            raise forms.ValidationError(
                "Телефон должен быть в формате +7XXXXXXXXXX или 8XXXXXXXXXX"
            )
        if User.objects.exclude(pk=self.instance.pk).filter(phone=phone).exists():
            raise forms.ValidationError("Пользователь с таким номером уже существует")
        return phone

    def clean_github_url(self):
        url = self.cleaned_data.get("github_url")
        if url and "github.com" not in url:
            raise forms.ValidationError("Ссылка должна вести на GitHub")
        return url


# --- Views ---
def register(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("projects:project_list")
    else:
        form = RegisterForm()
    return render(request, "users/register.html", {"form": form})


def user_login(request):
    if request.method == "POST":
        form = EmailAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect("projects:project_list")
    else:
        form = EmailAuthenticationForm()
    return render(request, "users/login.html", {"form": form})


def user_logout(request):
    logout(request)
    return redirect("projects:project_list")


def user_list(request):
    participants_list = User.objects.all().order_by("id")
    page_obj = get_paginator(participants_list, request, PAGINATOR_PER_PAGE)
    return render(request, "users/participants.html", {"page_obj": page_obj})


def user_detail(request, pk):
    user = get_object_or_404(User, pk=pk)
    return render(request, "users/user-details.html", {"user": user})


@login_required
def edit_profile(request, pk):
    user = get_object_or_404(User, pk=pk)
    if request.user != user:
        return redirect("users:user_detail", pk=pk)
    if request.method == "POST":
        form = EditProfileForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            form.save()
            return redirect("users:user_detail", pk=pk)
    else:
        form = EditProfileForm(instance=user)
    return render(request, "users/edit_profile.html", {"form": form})


@login_required
def change_password(request, pk):
    user = get_object_or_404(User, pk=pk)
    if request.user != user:
        return redirect("users:user_detail", pk=pk)
    if request.method == "POST":
        form = PasswordChangeForm(user, request.POST)
        if form.is_valid():
            form.save()
            return redirect("users:user_detail", pk=pk)
    else:
        form = PasswordChangeForm(user)
    return render(request, "users/change_password.html", {"form": form})
