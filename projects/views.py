import json
from http import HTTPStatus

from django import forms
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from django.core.paginator import Paginator

from .models import Project, Skill

AUTOCOMPLETE_LIMIT = 10
PAGINATOR_PER_PAGE = 12


# --- Форма проекта ---
class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ["name", "description", "github_url", "status"]

    def clean_github_url(self):
        url = self.cleaned_data.get("github_url")
        if url and "github.com" not in url:
            raise forms.ValidationError("Ссылка должна вести на GitHub")
        return url


def get_paginator(queryset, request):
    paginator = Paginator(queryset, PAGINATOR_PER_PAGE)
    page_number = request.GET.get("page")
    return paginator.get_page(page_number)


def get_object_or_json(model, **kwargs):
    obj = model.objects.filter(**kwargs).first()
    if obj is None:
        return None
    return obj


# --- Views ---
def redirect_to_project_list(request):
    return redirect("projects:project_list")


def project_list(request):
    skill_filter = request.GET.get("skill")
    projects = Project.objects.select_related("owner").order_by("-created_at")
    if skill_filter:
        projects = projects.filter(skills__name=skill_filter)
    all_skills = Skill.objects.all()

    page_obj = get_paginator(projects, request)

    context = {
        "projects": projects,
        "page_obj": page_obj,
        "all_skills": all_skills,
        "active_skill": skill_filter,
    }
    return render(request, "projects/project_list.html", context)


def project_detail(request, pk):
    project = Project.objects.select_related("owner").filter(pk=pk).first()
    if project is None:
        return render(request, "404.html", status=HTTPStatus.NOT_FOUND)
    return render(request, "projects/project-details.html", {"project": project})


@login_required
def create_project(request):
    if request.method == "POST":
        form = ProjectForm(request.POST)
        if form.is_valid():
            project = form.save(commit=False)
            project.owner = request.user
            project.save()
            project.participants.add(request.user)
            return redirect("projects:project_detail", pk=project.pk)
    else:
        form = ProjectForm()
    return render(
        request, "projects/create-project.html", {"form": form, "is_edit": False}
    )


@login_required
def edit_project(request, pk):
    project = get_object_or_json(Project, pk=pk)
    if project is None:
        return render(request, "404.html", status=HTTPStatus.NOT_FOUND)
    if request.user != project.owner:
        return redirect("projects:project_detail", pk=pk)
    if request.method == "POST":
        form = ProjectForm(request.POST, instance=project)
        if form.is_valid():
            form.save()
            return redirect("projects:project_detail", pk=pk)
    else:
        form = ProjectForm(instance=project)
    return render(
        request, "projects/create-project.html", {"form": form, "is_edit": True}
    )


@require_POST
@login_required
def toggle_participate(request, pk):
    project = get_object_or_json(Project, pk=pk)
    if project is None:
        return JsonResponse(
            {"status": "error", "message": "Проект не найден"},
            status=HTTPStatus.NOT_FOUND,
        )

    is_participant = project.participants.filter(pk=request.user.pk).exists()
    if is_participant:
        project.participants.remove(request.user)
    else:
        project.participants.add(request.user)

    return JsonResponse({"status": "ok", "participant": not is_participant})


@require_POST
@login_required
def complete_project(request, pk):
    project = get_object_or_json(Project, pk=pk)
    if project is None:
        return JsonResponse(
            {"status": "error", "message": "Проект не найден"},
            status=HTTPStatus.NOT_FOUND,
        )

    if request.user == project.owner and project.status == Project.STATUS_CHOICES[0][0]:
        project.status = Project.STATUS_CHOICES[1][0]
        project.save()
        return JsonResponse({"status": "ok", "project_status": project.status})

    return JsonResponse({"status": "error"}, status=HTTPStatus.FORBIDDEN)


@login_required
def skill_autocomplete(request):
    query = request.GET.get("q", "")
    skills = Skill.objects.filter(name__istartswith=query).order_by("name")[
        :AUTOCOMPLETE_LIMIT
    ]
    data = [{"id": skill.id, "name": skill.name} for skill in skills]
    return JsonResponse(data, safe=False)


@login_required
def skill_add(request, project_pk):
    project = get_object_or_json(Project, pk=project_pk)
    if project is None:
        return JsonResponse(
            {"status": "error", "message": "Проект не найден"},
            status=HTTPStatus.NOT_FOUND,
        )
    if request.user != project.owner:
        return JsonResponse({"status": "error"}, status=HTTPStatus.FORBIDDEN)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        data = request.POST

    skill_id = data.get("skill_id")
    name = data.get("name")
    created = False
    added = False

    if skill_id:
        skill = get_object_or_json(Skill, pk=skill_id)
        if skill is None:
            return JsonResponse(
                {"status": "error", "message": "Навык не найден"},
                status=HTTPStatus.NOT_FOUND,
            )
    elif name:
        skill, created = Skill.objects.get_or_create(name=name)
    else:
        return JsonResponse(
            {"status": "error", "message": "Нет данных"}, status=HTTPStatus.BAD_REQUEST
        )

    if not project.skills.filter(pk=skill.pk).exists():
        project.skills.add(skill)
        added = True

    return JsonResponse(
        {
            "skill_id": skill.pk,
            "name": skill.name,
            "created": created,
            "added": added,
        }
    )


@login_required
def skill_remove(request, project_pk, skill_pk):
    project = get_object_or_json(Project, pk=project_pk)
    if project is None:
        return JsonResponse(
            {"status": "error", "message": "Проект не найден"},
            status=HTTPStatus.NOT_FOUND,
        )

    skill = get_object_or_json(Skill, pk=skill_pk)
    if skill is None:
        return JsonResponse(
            {"status": "error", "message": "Навык не найден"},
            status=HTTPStatus.NOT_FOUND,
        )

    if request.user != project.owner:
        return JsonResponse({"status": "error"}, status=HTTPStatus.FORBIDDEN)

    if project.skills.filter(pk=skill_pk).exists():
        project.skills.remove(skill)
        return JsonResponse({"status": "ok"})

    return JsonResponse(
        {"status": "error", "message": "Навык не найден"}, status=HTTPStatus.BAD_REQUEST
    )
