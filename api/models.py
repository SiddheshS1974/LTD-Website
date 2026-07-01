from django.db import models
from django.contrib.auth.models import AbstractUser

class CustomUser(AbstractUser):
    ROLE_CHOICES = [
        ('New Member', 'New Member'),
        ('RMD', 'RMD'),
        ('Admin', 'Admin'),
    ]
    
    hgi_code = models.CharField(max_length=50, unique=True, null=True, blank=True)
    upline_rmd = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='downline')
    role = models.CharField(max_length=50, choices=ROLE_CHOICES, default='New Member')
    is_rmd = models.BooleanField(default=False)
    is_rmd_member = models.BooleanField(default=False)
    can_receive_requests = models.BooleanField(default=False)
    granted_pages = models.JSONField(default=list, blank=True)
    password_reset_token = models.CharField(max_length=200, null=True, blank=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"
    
class PendingUser(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    hgi_code = models.CharField(max_length=50)
    upline_rmd = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, related_name='pending_approvals')
    token = models.CharField(max_length=200, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_approved = models.BooleanField(default=False)


    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class ValidHGICode(models.Model):
    code = models.CharField(max_length=50, unique=True)
    first_name = models.CharField(max_length=100, blank=True, default='')
    last_name = models.CharField(max_length=100, blank=True, default='')
    upline_rmd_name = models.CharField(max_length=200, blank=True, default='')

    def __str__(self):
        return self.code


class ProtectedFile(models.Model):
    drive_file_id = models.CharField(max_length=200)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, default='')
    slug = models.SlugField(max_length=100, unique=True, null=True, blank=True)

    def __str__(self):
        return self.title


class RMDProfile(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    hgi_code = models.CharField(max_length=50, unique=True)
    user = models.OneToOneField(
        CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='rmd_profile'
    )

    def __str__(self):
        return f"{self.first_name} {self.last_name}"