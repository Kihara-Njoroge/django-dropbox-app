from django.urls import path

from . import views

urlpatterns = [
    path('', views.listfolder, name='index'),
    path('folder/<path:url>/', views.listfolder, name='folder'),
    path('file/<path:name>', views.download, name='file'),
    path('upload/', views.upload, name='upload'),
    path('delete/<path:path>/', views.delete, name='delete'),
    path('newfolder/', views.newfolder, name='newfolder'),
    path('auth/', views.request_access, name='auth'),
    path('confirm/', views.confirm_access, name='confirm'),
]
