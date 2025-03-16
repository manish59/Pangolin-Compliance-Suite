from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    # Class-based view URL
    path('', views.DashboardView.as_view(), name='dashboard'),

    # Alternatively, you can use the function-based view
    # path('', views.dashboard_view, name='dashboard'),
]