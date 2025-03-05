from django.urls import path
from . import views


app_name = 'environments'

urlpatterns = [
    path('', views.EnvironmentListView.as_view(), name='environment_list'),
    path('create/', views.EnvironmentCreateView.as_view(), name='environment_create'),
    path('<uuid:pk>/', views.EnvironmentDetailView.as_view(), name='environment_detail'),
    path('<uuid:pk>/update/', views.EnvironmentUpdateView.as_view(), name='environment_update'),
    path('<uuid:pk>/delete/', views.EnvironmentDeleteView.as_view(), name='environment_delete'),
    # path('<uuid:pk>/toggle/', views.EnvironmentDeleteView.as_view(), name='environment_delete'),
]