from django.contrib.auth.base_user import AbstractBaseUser
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication

from user.serializers import UserSerializer


class CreateUserView(generics.CreateAPIView[AbstractBaseUser]):
    serializer_class = UserSerializer


class ManageUserView(generics.RetrieveUpdateAPIView[AbstractBaseUser]):
    serializer_class = UserSerializer
    authentication_classes = (JWTAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get_object(self) -> AbstractBaseUser:
        return self.request.user
