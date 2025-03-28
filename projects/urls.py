from django.urls import path
from . import views

app_name = "projects"

urlpatterns = [
    # Project list view - main page with the table and search functionality
    path('', views.ProjectListView.as_view(), name='project_list'),

    # Project detail view - accessed via the "Choose" button
    path('<uuid:pk>/', views.ProjectDetailView.as_view(), name='project_detail'),

    # Project creation view - accessed via the "Create Project" button
    path('create/', views.ProjectCreateView.as_view(), name='project_create'),
    path('<uuid:pk>/update/', views.ProjectUpdateView.as_view(), name='project_update'),

    # # Additional URLs that might be useful for your project management app
    # path('<int:pk>/update/', views.ProjectUpdateView.as_view(), name='project_update'),
    # path('<int:pk>/delete/', views.ProjectDeleteView.as_view(), name='project_delete'),
]