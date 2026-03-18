from django.urls import path
from . import views

urlpatterns = [
    path('students/', views.studentsView),
    path('students/<int:pk>/', views.studentDetailView),
    path('login/', views.login_view),
    path('rmds/', views.rmd_list),
    path('register/', views.register_request),
    path('approve/<str:token>/', views.approve_request),
    path('deny/<str:token>/', views.deny_request),
    path('verify-token/<str:token>/', views.verify_token),
    path('setup-account/', views.setup_account),
]