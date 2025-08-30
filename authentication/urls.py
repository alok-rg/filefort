# urls for authentication

from django.urls import path
from authentication import views

urlpatterns = [
    path('login/', views.login_idx, name='login'),
    path('register/', views.register, name='register'),
    path('logout/', views.logout_view, name='logout'),
]