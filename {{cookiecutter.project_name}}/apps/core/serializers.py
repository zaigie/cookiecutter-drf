import re
from rest_framework import serializers

from core.models import User, Group


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


class LoginOrRegisterSerializer(serializers.Serializer):
    phone = serializers.CharField(max_length=11)
    verification_code = serializers.CharField(max_length=6)

    def create(self, validated_data):
        user, created = User.objects.get_or_create(
            phone=validated_data["phone"],
            defaults={"username": validated_data["phone"]},
        )
        return user


class PhoneVerificationSerializer(serializers.Serializer):
    phone = serializers.CharField(max_length=11)

    def validate_phone(self, phone):
        pattern = re.compile(r"^1[3-9]\d{9}$")
        if not pattern.match(phone):
            raise serializers.ValidationError("无效的手机号")
        return phone


# class VerificationSerializer(serializers.Serializer):
#     validation_type = serializers.CharField(max_length=10)
#     verification = serializers.CharField(max_length=50)

#     def validate_verification(self, verification):
#         validation_type = self.initial_data["validation_type"]
#         if validation_type == "email":
#             return verification
#         elif validation_type == "phone":
#             pattern = re.compile(r"^1[3-9]\d{9}$")
#             if not pattern.match(verification):
#                 raise serializers.ValidationError("无效的手机号")
#         return verification
