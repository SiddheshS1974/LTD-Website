from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser

class CustomUserAdmin(UserAdmin):
    model = CustomUser
    fieldsets = UserAdmin.fieldsets + (
        ('Extra Fields', {'fields': ('hgi_code', 'upline_rmd', 'role', 'is_rmd')}),
    )

admin.site.register(CustomUser, CustomUserAdmin)