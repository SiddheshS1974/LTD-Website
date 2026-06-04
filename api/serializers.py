from rest_framework import serializers
from students.models import Student
from .models import CustomUser, ValidHGICode, ProtectedFile

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
            'role', 'hgi_code', 'upline_rmd_name',
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