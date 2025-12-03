from django.urls import path
from . import views

from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('register/', views.register_view, name='register'),
    path('scan/', views.scan_view, name='scan'),
    path('gallery/', views.gallery_view, name='gallery'),
    path('delete_face/<int:face_id>/', views.delete_face, name='delete_face'),
    path('edit_face/<int:face_id>/', views.edit_face, name='edit_face'),
    path('video_feed/', views.video_feed, name='video_feed'),
    path('get_recognized_faces/', views.get_recognized_faces, name='get_recognized_faces'),
]
