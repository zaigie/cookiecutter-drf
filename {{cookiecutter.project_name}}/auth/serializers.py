from rest_framework import serializers
from rest_framework.validators import UniqueValidator
from utils.custom.exceptions import APIError
from utils.files_func import get_cos_url
from utils.tools import weeks_range
from utils.validators import is_email, is_phone

from user.models import Character, Task, User


class CharacterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Character
        exclude = ["character_id"]


class RegisterSendSerializer(serializers.Serializer):
    type = serializers.IntegerField()
    value = serializers.CharField()

    def validate(self, attrs):
        type = attrs.get("type")
        value = attrs.get("value")
        if type == 1 and not is_phone(value):
            raise APIError("请输入正确的手机号")
        if type == 2 and not is_email(value):
            raise APIError("请输入正确的邮箱")
        return attrs


class RegisterSerializer(serializers.ModelSerializer):
    username = serializers.CharField(
        min_length=5,
        max_length=15,
        error_messages={"min_length": "用户名长度不低于5个字符", "max_length": "用户名长度不超过15个字符"},
        validators=[UniqueValidator(queryset=User.objects.all(), message="用户名不能重复")],
    )
    validator_type = serializers.IntegerField()
    captcha = serializers.IntegerField()

    class Meta:
        model = User
        fields = [
            "user_id",
            "username",
            "nickname",
            "password",
            "phone",
            "email",
            "validator_type",
            "captcha",
        ]
        extra_kwargs = {
            "nickname": {
                "default": "未设置昵称",
                "max_length": 24,
                "error_messages": {"max_length": "昵称长度不超过24个字符"},
            },
            "phone": {
                "required": False,
                "allow_null": True,
            },
            "email": {
                "required": False,
                "allow_null": True,
            },
        }

    def validate(self, attrs):
        validator_type = attrs.get("validator_type")
        phone = attrs.get("phone")
        email = attrs.get("email")
        if validator_type == 1 and not phone:
            raise APIError("请输入正确的手机号")
        if validator_type == 2 and not email:
            raise APIError("请输入正确的邮箱")
        return attrs

    def create(self, validated_data):
        del validated_data["validator_type"]
        del validated_data["captcha"]
        return super().create(validated_data)


class UserLoginSerializer(serializers.Serializer):
    verify = serializers.CharField()
    password = serializers.CharField()


class UserSerializer(serializers.ModelSerializer):
    avatar = serializers.SerializerMethodField()
    character = serializers.SerializerMethodField()
    opern_num = serializers.SerializerMethodField()
    resource_num = serializers.SerializerMethodField()
    collection_num = serializers.SerializerMethodField()
    vip_expire_time = serializers.DateTimeField(format="%Y-%m-%d", read_only=True)
    birthday = serializers.DateField(format="%Y-%m-%d", read_only=True)
    last_login = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", read_only=True)
    create_time = serializers.DateTimeField(
        source="date_joined", read_only=True, format="%Y-%m-%d %H:%M:%S"
    )

    class Meta:
        model = User
        fields = [
            "user_id",
            "username",
            "nickname",
            "avatar",
            "character",
            "sex",
            "description",
            "area",
            "birthday",
            "phone",
            "email",
            "opern_num",
            "resource_num",
            "collection_num",
            "vip_expire_time",
            "last_login",
            "create_time",
        ]

    def get_avatar(self, obj):
        if obj.avatar_key:
            return get_cos_url(obj.avatar_key)
        return None

    def get_character(self, obj):
        if obj.character:
            result = CharacterSerializer(instance=obj.character)
            return result.data
        return None

    def get_opern_num(self, obj):
        return obj.user_operns.count()

    def get_resource_num(self, obj):
        resources_count = 0
        for opern in obj.user_operns.all():
            resources_count += opern.opern_resources.count()
        return resources_count

    def get_collection_num(self, obj):
        return obj.user_collections.count()

    def validate_sex(self, value):
        if value not in [0, 1, 2]:
            raise serializers.ValidationError("只接受0/1/2为值的性别值")
        return value


class UserModifySerializer(serializers.ModelSerializer):
    birthday = serializers.DateField(format="%Y-%m-%d", required=False)

    class Meta:
        model = User
        fields = ["nickname", "sex", "description", "area", "birthday"]
        extra_kwargs = {
            "nickname": {
                "required": False,
                "max_length": 24,
                "error_messages": {"max_length": "昵称长度不超过24个字符"},
            },
            "area": {"required": False},
            "description": {
                "required": False,
                "allow_null": True,
                "max_length": 32,
                "error_messages": {"max_length": "简介长度不超过32个字符"},
            },
        }

    def validate_sex(self, value):
        if value not in [0, 1, 2]:
            raise serializers.ValidationError("只接受0/1/2为值的性别值")
        return value


class UserAvatarSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["avatar_key"]
        extra_kwargs = {
            "avatar_key": {
                "required": False,
                "write_only": True,
                "allow_null": True,
            },
        }


class TaskSerializer(serializers.ModelSerializer):

    weeks = serializers.SerializerMethodField()

    class Meta:
        model = Task
        fields = ["task_id", "target", "progress", "weeks", "user"]
        extra_kwargs = {
            "target": {
                "min_value": 1,
                "max_value": 5040,
                "error_messages": {
                    "min_value": "弹奏目标不能低于1分钟",
                    "max_value": "弹奏目标不能超过5040分钟",
                },
            },
            "task_id": {"write_only": True},
            "progress": {"default": 0},
            "user": {"write_only": True},
        }

    def get_weeks(self, obj):
        """根据创建时间返回该周的起始和结束日"""
        return weeks_range(obj.create_time)
