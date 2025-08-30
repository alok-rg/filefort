from django.urls import path
from dashboard import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', views.index, name='index'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('upload/', views.upload_file, name='upload_file'),
    path('group_create/', views.group_create, name='group_create'),
    path('fetch_tables/', views.fetch_tables, name='fetch_tables'),
    path('update_access/', views.update_access, name='update_access'),
    path('delete_file/', views.delete_file, name='delete_file'),
    path('delete_group/', views.delete_group, name='delete_group'),
    path('pdf/view/<str:file_id>/', views.pdf_viewer, name='pdf_viewer'),
    path('pdf/stream/<str:token>/', views.serve_pdf, name='serve_pdf'),
    path('search_user/', views.search_user, name='search_user'),
    path('update_role/', views.update_role, name='update_role'),
]
