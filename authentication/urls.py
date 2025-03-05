from django.urls import path
from . import views

app_name = 'authentication'

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('oauth2/callback/', views.oauth2_callback, name='oauth2_callback'),
    path('openid/callback/', views.openid_callback, name='openid_callback'),
]