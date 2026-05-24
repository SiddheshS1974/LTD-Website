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
    path('check-username/', views.check_username),
    path('setup-account/', views.setup_account),
    path('forgot-password/', views.forgot_password),
    path('verify-reset-token/<str:token>/', views.verify_reset_token),
    path('reset-password/', views.reset_password),
    path('logout/', views.logout_view),
    path('users/', views.user_list),
    path('users/<int:pk>/delete/', views.delete_user),
    path('users/<int:pk>/role/', views.change_user_role),
    path('rmd/members/', views.rmd_member_list),
    path('hgi-codes/', views.hgi_codes_list),
    path('hgi-codes/<int:pk>/', views.hgi_code_detail),
]