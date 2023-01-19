from uuid import uuid4

from django.contrib.auth.hashers import make_password
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from rest_framework import mixins
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.status import HTTP_201_CREATED
from rest_framework.viewsets import GenericViewSet
from rest_framework_simplejwt.tokens import RefreshToken
from custom.exceptions import CustomAPIError
from utils.redis_func import Client as RedisClient
from utils.verify import send_email, send_sms

from auth.models import User
import auth.serializers as serializers


class UserViewSet(
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    GenericViewSet,
):
    lookup_field = "username"
    queryset = User.query.all()
    serializer_class = serializers.UserSerializer


class LoginView(GenericViewSet):
    authentication_classes = []
    permission_classes = []
    queryset = User.query.all()

    def get_serializer_class(self):
        if self.action == "email":
            return serializers.EmailLoginSerializer
        elif self.action == "phone":
            return serializers.PhoneLoginSerializer
        return serializers.BasicLoginSerializer

    def auth(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        verification_type = self.action
        verification = serializer.validated_data.get(verification_type)
        password = serializer.validated_data.get("password")
        user = User.query(**{verification_type: verification}).first()
        if not (user and user.check_password(password)):
            raise CustomAPIError(
                _("The user does not exist or the password is incorrect.")
            )

        user.update_last_login()
        refresh = RefreshToken.for_user(user)
        data = {
            "username": user.username,
            "token": str(refresh.access_token),
            "refresh_token": str(refresh),
        }
        return Response(data)

    @action(methods=["POST"], detail=False)
    def basic(self, request, *args, **kwargs):
        return self.auth(request, *args, **kwargs)

    @action(methods=["POST"], detail=False)
    def phone(self, request, *args, **kwargs):
        return self.auth(request, *args, **kwargs)

    @action(methods=["POST"], detail=False)
    def email(self, request, *args, **kwargs):
        return self.auth(request, *args, **kwargs)


class RegisterViewSet(mixins.CreateModelMixin, GenericViewSet):

    authentication_classes = []
    permission_classes = []
    queryset = User.query.all()

    def get_serializer_class(self):
        if self.action == "email":
            return serializers.EmailRegisterSerializer
        elif self.action == "phone":
            return serializers.PhoneRegisterSerializer
        if settings.ALLOW_FREE_REGISTION:
            return serializers.UserSerializer
        raise CustomAPIError(_("Unsupported registration authentication mode."))

    def create(self, request, *args, **kwargs):
        password = make_password(request.data["password"])
        request.data["password"] = password

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=HTTP_201_CREATED, headers=headers)

    def perform_create(self, serializer):
        if self.serializer_class != serializers.UserSerializer:
            self.verification(self.request)
        serializer.save()

    def verification(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        verification_type = self.action
        verification = serializer.validated_data.get(verification_type)
        verification_code = serializer.validated_data.get("verification_code")

        r = RedisClient()
        key = f"register_{verification}"
        if r.get(key):
            if str(verification_code) == r.get(key):
                r.delete(key)
            else:
                raise CustomAPIError(_("Verification code error"))
        else:
            raise CustomAPIError(
                _("The verification code does not exist or has expired")
            )


class VerificationSendViewSet(GenericViewSet):

    authentication_classes = []
    permission_classes = []

    def get_serializer_class(self):
        if self.action == "email":
            return serializers.EmailVerificationSerializer
        elif self.action == "phone":
            return serializers.PhoneVerificationSerializer
        raise CustomAPIError(_("Unsupported registration authentication mode."))

    def send(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        verification_type = self.action
        verification = serializer.validated_data.get(verification_type)

        if User.query(
            **{self.verification_types[verification_type]["var"]: verification}
        ).first():
            raise CustomAPIError("The user already exists.")

        verification_code = str(uuid4())[:6]

        if verification_type == "email":
            send_email(verification, verification_code, "register")
        elif verification_type == "phone":
            send_sms(verification, verification_code, "register")

        return Response({"message": _("Verification code sent successfully.")})

    @action(methods=["POST"], detail=False)
    def phone(self, request, *args, **kwargs):
        return self.send(request, *args, **kwargs)

    @action(methods=["POST"], detail=False)
    def email(self, request, *args, **kwargs):
        return self.send(request, *args, **kwargs)
