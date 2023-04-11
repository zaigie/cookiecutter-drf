from django.urls import path, include
from core.views import (
    UserViewSet,
    CreateUserView,
    LoginView,
    UserVerificationUpdateViewSet,
    UserPasswordUpdateViewSet,
    VerificationViewSet,
)
from rest_framework_nested import routers

router = routers.DefaultRouter()
router.register(r"users", UserViewSet, basename="user")
user_router = routers.NestedDefaultRouter(router, r"users", lookup="user")
user_router.register(
    r"validation", UserVerificationUpdateViewSet, basename="user-verification-update"
)
user_router.register(
    r"password", UserPasswordUpdateViewSet, basename="user-password-update"
)

urlpatterns = [
    path(r"users/", CreateUserView.as_view()),
    path(r"login/", LoginView.as_view()),
    path(r"validation/", VerificationViewSet.as_view()),
    path(r"", include(router.urls)),
    path(r"", include(user_router.urls)),
]
