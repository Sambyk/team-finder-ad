from django.urls import path
from . import views

urlpatterns = [
    path('', views.redirect_to_project_list),
    path('project/list/', views.project_list, name='project_list'),
    path('project/create-project/', views.create_project, name='create_project'),
    path('project/<int:pk>/', views.project_detail, name='project_detail'),
    path('project/<int:pk>/edit/', views.edit_project, name='edit_project'),
    path('project/<int:pk>/toggle-participate/', views.toggle_participate, name='toggle_participate'),
    path('project/<int:pk>/complete/', views.complete_project, name='complete_project'),
    path('project/skills/', views.skill_autocomplete, name='skill_autocomplete'),
    path('project/<int:project_pk>/skills/add/', views.skill_add, name='skill_add'),
    path('project/<int:project_pk>/skills/<int:skill_pk>/remove/', views.skill_remove, name='skill_remove'),
]
