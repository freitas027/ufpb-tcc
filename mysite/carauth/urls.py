from django.urls import path

from . import views

urlpatterns = [
    path('index/', views.index, name='index'),
    path('post/', views.post_test, name='post'),
    path('user/', views.add_user, name='user'),
    path('register/', views.assign_tag, name='register'),
    path('remove-assignment/', views.remove_assign, name='remove-assign'),
    path('remove-reader-assignment/', views.remove_reader_assignment, name ='remove-reader-assignment'),
    #path('new-tag/', views.new_tag, name='new-tag'),
    path('view-assignment/<int:page>/', views.view_tag_assignments, name='view-assignments'),
    path('hello/', views.hello, name='hello'),
    path('time/<str:mac>/', views.get_time, name='time'),
    path('new-ard-assign/', views.new_ard_assign, name ='new-ard-assign'),
    path('new-car/', views.new_car, name='new-car'),
    path('post-loc/', views.post_location, name='post-loc'),
    path('', views.hello),
    path('path/<int:login_id>/', views.get_login_gapi_path, name='gapi-path'),

]