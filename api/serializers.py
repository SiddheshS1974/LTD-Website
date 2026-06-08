from rest_framework import serializers
from students.models import Student
from .models import CustomUser, ValidHGICode, ProtectedFile, RMDProfile

class StudentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Student
        fields = "__all__"

class CustomUserSerializer(serializers.ModelSerializer):
    upline_rmd_name = serializers.SerializerMethodField()

    class Meta:
        model = CustomUser
        fields = [
            'id', 'username', 'first_name', 'last_name', 'email',
            'is_staff', 'is_active', 'date_joined', 'last_login',
            'role', 'hgi_code', 'upline_rmd_name', 'is_rmd_member', 'can_receive_requests',
        ]

    def get_upline_rmd_name(self, obj):
        if obj.upline_rmd:
            name = f"{obj.upline_rmd.first_name} {obj.upline_rmd.last_name}".strip()
            return name or obj.upline_rmd.username
        return None


class ValidHGICodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ValidHGICode
        fields = ['id', 'code', 'first_name', 'last_name', 'upline_rmd_name']


class ProtectedFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProtectedFile
        fields = ['id', 'title', 'description']


class RMDProfileSerializer(serializers.ModelSerializer):
    is_claimed = serializers.SerializerMethodField()
    user_id = serializers.SerializerMethodField()
    username = serializers.SerializerMethodField()
    email = serializers.SerializerMethodField()
    is_active = serializers.SerializerMethodField()
    can_receive_requests = serializers.SerializerMethodField()
    last_login = serializers.SerializerMethodField()
    date_joined = serializers.SerializerMethodField()

    class Meta:
        model = RMDProfile
        fields = [
            'id', 'first_name', 'last_name', 'hgi_code', 'is_claimed',
            'user_id', 'username', 'email', 'is_active', 'can_receive_requests',
            'last_login', 'date_joined',
        ]

    def get_is_claimed(self, obj): return obj.user_id is not None
    def get_user_id(self, obj): return obj.user_id
    def get_username(self, obj): return obj.user.username if obj.user else None
    def get_email(self, obj): return obj.user.email if obj.user else None
    def get_is_active(self, obj): return obj.user.is_active if obj.user else None
    def get_can_receive_requests(self, obj): return obj.user.can_receive_requests if obj.user else False
    def get_last_login(self, obj): return obj.user.last_login if obj.user else None
    def get_date_joined(self, obj): return obj.user.date_joined if obj.user else None