from rest_framework import serializers
from rest_framework.validators import UniqueValidator

from auth.models import User, Group


class GroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        exclude = ["is_staff", "is_active", "user_permissions"]
        read_only_fields = [
            "id",
            "username",
            "last_login",
            "date_joined",
            "is_superuser",
        ]
        extra_kwargs = {"password": {"write_only": True}}


class EmailRegisterSerializer(UserSerializer):
    email = serializers.EmailField(
        validators=[UniqueValidator(queryset=User.query.all())]
    )


class PhoneRegisterSerializer(UserSerializer):
    phone = serializers.CharField(
        validators=[UniqueValidator(queryset=User.query.all())]
    )


class VerificationSerializer(serializers.Serializer):
    verification_code = serializers.CharField()


class EmailVerificationSerializer(VerificationSerializer):
    email = serializers.EmailField(
        validators=[UniqueValidator(queryset=User.query.all())]
    )


class PhoneVerificationSerializer(VerificationSerializer):
    phone = serializers.CharField(
        validators=[UniqueValidator(queryset=User.query.all())]
    )


class LoginSerializer(serializers.Serializer):
    password = serializers.CharField()


class BasicLoginSerializer(LoginSerializer):
    username = serializers.CharField()


class EmailLoginSerializer(LoginSerializer):
    email = serializers.EmailField()


class PhoneLoginSerializer(LoginSerializer):
    phone = serializers.CharField()
