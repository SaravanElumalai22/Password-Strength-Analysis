from django.urls import path
from .views import home,index, profile, RegisterView,logout_view
from . import views

urlpatterns = [
    path('', home, name='users-home'),
    path('register/', RegisterView.as_view(), name='users-register'),
    path('profile/', profile, name='users-profile'),
    path('detect/', views.detect, name='detect'),
    path('result/', views.detect_output, name='detect_result'),
    path('history/', views.detect_db, name='detect_db'),
    path('logout_view/',logout_view,name='logout_view'),
    path('index/', index, name='users-index'),
    path('profile_list/',views.profile_list,name='profile_list'),
    path('history/', views.detect_db, name='detect_db'),
    
    
    ]


 