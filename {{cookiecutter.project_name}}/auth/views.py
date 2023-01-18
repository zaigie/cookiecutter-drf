import datetime
from uuid import uuid4

from django.contrib.auth.hashers import make_password
from myopern.settings import CAPTCHA_EXPIRES, CAPTCHA_RESEND
from rest_framework import mixins
from rest_framework.decorators import action
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework.status import HTTP_201_CREATED
from rest_framework.viewsets import GenericViewSet
from rest_framework_simplejwt.tokens import RefreshToken
from utils.custom.exceptions import APIError
from utils.files_func import CosClient
from utils.redis_func import MyRedis
from utils.send import send_email, send_sms
from utils.tools import generate_captcha, generate_id, weeks_range
from utils.validators import is_date, is_email, is_phone

from user.models import User
from user.serializers import (
    RegisterSendSerializer,
    RegisterSerializer,
    TaskSerializer,
    UserAvatarSerializer,
    UserLoginSerializer,
    UserModifySerializer,
    UserSerializer,
)


class UserViewSet(mixins.RetrieveModelMixin, mixins.UpdateModelMixin, GenericViewSet):
    lookup_field = "username"

    def get_serializer_class(self):
        if self.action in ["update", "partial_update"]:
            return UserModifySerializer
        elif self.action == "set_avatar":
            return UserAvatarSerializer
        return UserSerializer

    def get_queryset(self):
        return User.objects.filter(username=self.request.user.username)

    @action(methods=["POST"], detail=True, url_path="avatar")
    def set_avatar(self, request, username=None):
        user = request.user
        old_key = user.avatar_key
        cos_client = CosClient()
        if old_key is not None:
            cos_client.delete(old_key)

        file = request.FILES.get("file")
        if not file:
            update_data = {"avatar_key": None}
        else:
            extend = (file.name).split(".")[-1].lower()
            # if extend not in COS_ALLOWED_EXT:
            #     raise APIError("请上传允许的图像格式文件")
            filename = "avatar-" + uuid4().hex + f".{extend}"
            key = f"avatar/{user.user_id}/{filename}"
            cos_client.upload(key, file)
            update_data = {"avatar_key": key}

        serializer = self.get_serializer(user, data=update_data)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        return Response(serializer.data)


class LoginView(GenericAPIView):
    authentication_classes = []
    permission_classes = []
    serializer_class = UserLoginSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        verify = serializer.validated_data["verify"]
        password = serializer.validated_data["password"]
        if is_phone(verify):
            user = User.query_by_phone(verify)
            if user is None:
                raise APIError("手机号未注册")
        elif is_email(verify):
            user = User.query_by_email(verify)
            if user is None:
                raise APIError("邮箱未注册")
        else:
            user = User.query_by_username(verify)
        if not (user and user.check_password(password)):
            raise APIError("用户不存在或密码错误")
        user.update_last_login()
        refresh = RefreshToken.for_user(user)
        data = {
            "username": user.username,
            "token": str(refresh.access_token),
            "refresh_token": str(refresh),
        }
        return Response(data)


class RegisterViewSet(mixins.CreateModelMixin, GenericViewSet):
    authentication_classes = []
    permission_classes = []
    types = {
        1: {"name": "手机号", "var": "phone", "func_name": "send_sms"},
        2: {"name": "邮箱", "var": "email", "func_name": "send_email"},
    }

    def get_serializer_class(self):
        if self.action == "send_captcha":
            return RegisterSendSerializer
        return RegisterSerializer

    def create(self, request, *args, **kwargs):
        request.data["user_id"] = "U" + generate_id()
        password = make_password(request.data["password"])
        request.data["password"] = password
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        user = User.query_by_id(request.data["user_id"])
        serializer = UserSerializer(user)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=HTTP_201_CREATED, headers=headers)

    def perform_create(self, serializer):
        validator_type = serializer.validated_data["validator_type"]
        value = serializer.validated_data[self.types[validator_type]["var"]]
        captcha = serializer.validated_data["captcha"]
        if validator_type not in list(self.types.keys()):
            raise APIError("不支持的注册验证方式")
        if User.query_by_phone(value) or User.query_by_email(value):
            raise APIError(f"{self.types[type]['name']}已被注册")
        r = MyRedis()
        reg_key = f"reg_{value}"
        if r.get(reg_key):
            if str(captcha) == r.get(reg_key):
                serializer.save()
                User.set_character(serializer.validated_data["username"])
                r.delete(reg_key)
            else:
                raise APIError("验证码错误")
        else:
            raise APIError("验证码不存在或已过期")

    @action(methods=["POST"], detail=False, url_path="send")
    def send_captcha(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        type = serializer.validated_data["type"]
        value = serializer.validated_data["value"]
        if type not in list(self.types.keys()):
            raise APIError("不支持的注册验证方式")
        if User.query_by_phone(value) or User.query_by_email(value):
            raise APIError(f"{self.types[type]['name']}已被注册")
        captcha = generate_captcha()
        r = MyRedis()
        reg_key = f"reg_{value}"
        if r.get(reg_key):
            expires = int(r.get_expired(reg_key))
            if expires > CAPTCHA_EXPIRES:
                r.delete(reg_key)
                eval(self.types[type]["func_name"])(value, captcha, "reg")
                return Response({})
            resend_time = str(CAPTCHA_RESEND - expires)
            raise APIError(f"请{resend_time}s后再重新发送")
        eval(self.types[type]["func_name"])(value, captcha, "reg")
        return Response({})


class TaskViewSet(
    mixins.RetrieveModelMixin,
    GenericViewSet,
):
    lookup_field = "task_id"
    serializer_class = TaskSerializer

    def get_queryset(self):
        return self.request.user.user_tasks.all()

    @action(methods=["POST", "PUT"], detail=False, url_path="set")
    def create_or_update(self, request, *args, **kwargs):
        request.data["task_id"] = "T" + generate_id()
        request.data["user"] = request.user.user_id
        exists_task = request.user.user_tasks.all().order_by("-create_time").first()
        if exists_task and weeks_range(datetime.datetime.now()) == weeks_range(
            exists_task.create_time
        ):
            serializer = self.get_serializer(
                instance=exists_task,
                data={"target": request.data["target"]},
                partial=True,
            )
        else:
            serializer = self.get_serializer(data=request.data)

        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    @action(methods=["GET"], detail=False)
    def current(self, request, *args, **kwargs):
        date_range = request.query_params.get("date_range")
        if date_range:
            if not is_date(date_range):
                raise APIError("日期参数格式错误：%Y-%m-%d")
            query_date = datetime.datetime.strptime(date_range, "%Y-%m-%d")
            dt_s, dt_e = weeks_range(query_date, format="datetime")
            task = self.get_queryset().filter(create_time__range=[dt_s, dt_e]).first()
        else:
            task = self.get_queryset().order_by("-create_time").first()
        if not task:
            return Response({})
        serializer = self.get_serializer(instance=task)
        return Response(serializer.data)
