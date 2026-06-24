import json
from django import forms
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from django.core.paginator import Paginator
from .models import Project, Skill


# --- Форма проекта ---
class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ['name', 'description', 'github_url', 'status']

    def clean_github_url(self):
        url = self.cleaned_data.get('github_url')
        if url and 'github.com' not in url:
            raise forms.ValidationError('Ссылка должна вести на GitHub')
        return url


# --- Views ---
def redirect_to_project_list(request):
    return redirect('projects:project_list')


def project_list(request):
    skill_filter = request.GET.get('skill')
    projects = Project.objects.all().order_by('-created_at')
    if skill_filter:
        projects = projects.filter(skills__name=skill_filter)
    all_skills = Skill.objects.all()
    
    paginator = Paginator(projects, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'projects': projects,
        'page_obj': page_obj,
        'all_skills': all_skills,
        'active_skill': skill_filter,
    }
    return render(request, 'projects/project_list.html', context)


def project_detail(request, pk):
    project = get_object_or_404(Project, pk=pk)
    return render(request, 'projects/project-details.html', {'project': project})


@login_required
def create_project(request):
    if request.method == 'POST':
        form = ProjectForm(request.POST)
        if form.is_valid():
            project = form.save(commit=False)
            project.owner = request.user
            project.save()
            project.participants.add(request.user)
            return redirect('projects:project_detail', pk=project.pk)
    else:
        form = ProjectForm()
    return render(request, 'projects/create-project.html', {'form': form, 'is_edit': False})


@login_required
def edit_project(request, pk):
    project = get_object_or_404(Project, pk=pk)
    if request.user != project.owner:
        return redirect('projects:project_detail', pk=pk)
    if request.method == 'POST':
        form = ProjectForm(request.POST, instance=project)
        if form.is_valid():
            form.save()
            return redirect('projects:project_detail', pk=pk)
    else:
        form = ProjectForm(instance=project)
    return render(request, 'projects/create-project.html', {'form': form, 'is_edit': True})


@require_POST
@login_required
def toggle_participate(request, pk):
    project = get_object_or_404(Project, pk=pk)
    if request.user in project.participants.all():
        project.participants.remove(request.user)
        is_participant = False
    else:
        project.participants.add(request.user)
        is_participant = True
    return JsonResponse({'status': 'ok', 'participant': is_participant})


@require_POST
@login_required
def complete_project(request, pk):
    project = get_object_or_404(Project, pk=pk)
    if request.user == project.owner and project.status == 'open':
        project.status = 'closed'
        project.save()
        return JsonResponse({'status': 'ok', 'project_status': 'closed'})
    return JsonResponse({'status': 'error'}, status=403)


@login_required
def skill_autocomplete(request):
    q = request.GET.get('q', '')
    skills = Skill.objects.filter(name__istartswith=q).order_by('name')[:10]
    data = [{'id': s.id, 'name': s.name} for s in skills]
    return JsonResponse(data, safe=False)


@login_required
def skill_add(request, project_pk):
    project = get_object_or_404(Project, pk=project_pk)
    if request.user != project.owner:
        return JsonResponse({'status': 'error'}, status=403)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        data = request.POST

    skill_id = data.get('skill_id')
    name = data.get('name')
    created = False
    added = False

    if skill_id:
        skill = get_object_or_404(Skill, pk=skill_id)
    elif name:
        skill, created = Skill.objects.get_or_create(name=name)
    else:
        return JsonResponse({'status': 'error', 'message': 'Нет данных'}, status=400)

    if not project.skills.filter(pk=skill.pk).exists():
        project.skills.add(skill)
        added = True

    return JsonResponse({
        'skill_id': skill.pk,
        'name': skill.name,
        'created': created,
        'added': added,
    })


@login_required
def skill_remove(request, project_pk, skill_pk):
    project = get_object_or_404(Project, pk=project_pk)
    skill = get_object_or_404(Skill, pk=skill_pk)
    if request.user != project.owner:
        return JsonResponse({'status': 'error'}, status=403)
    if project.skills.filter(pk=skill_pk).exists():
        project.skills.remove(skill)
        return JsonResponse({'status': 'ok'})
    return JsonResponse({'status': 'error', 'message': 'Навык не найден'}, status=400)
