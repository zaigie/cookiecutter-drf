from django.urls import path, include
from user.views import UserViewSet, LoginView, RegisterViewSet, TaskViewSet
from rest_framework_nested import routers

router = routers.DefaultRouter()
router.register(r"register", RegisterViewSet, basename="user")

router.register(r"users", UserViewSet, basename="user")
user_router = routers.NestedDefaultRouter(router, r"users", lookup="user")
user_router.register(r"tasks", TaskViewSet, basename="task")

urlpatterns = [
    path(r"", include(router.urls)),
    path(r"", include(user_router.urls)),
    path(r"login/", LoginView.as_view()),
]
