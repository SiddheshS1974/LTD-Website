from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, PendingUser, ValidHGICode

class CustomUserAdmin(UserAdmin):
    model = CustomUser
    fieldsets = UserAdmin.fieldsets + (
        ('Extra Fields', {'fields': ('hgi_code', 'upline_rmd', 'role', 'is_rmd')}),
    )

@admin.register(PendingUser)
class PendingUserAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'email', 'hgi_code', 'upline_rmd', 'is_approved', 'created_at')
    list_filter = ('is_approved',)
    search_fields = ('email', 'hgi_code', 'first_name', 'last_name')

@admin.register(ValidHGICode)
class ValidHGICodeAdmin(admin.ModelAdmin):
    list_display = ('code', 'first_name', 'last_name', 'upline_rmd_name')
    search_fields = ('code', 'first_name', 'last_name')

admin.site.register(CustomUser, CustomUserAdmin)