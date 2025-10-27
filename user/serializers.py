from typing import Any, Dict

from django.contrib.auth import get_user_model
from django.contrib.auth.base_user import AbstractBaseUser
from rest_framework import serializers


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = get_user_model()
        fields = ("id", "email", "password", "is_staff")
        read_only_fields = ("id", "is_staff")
        extra_kwargs = {"password": {"write_only": True, "min_length": 5}}

    def create(self, validated_data: Dict[str, Any]) -> AbstractBaseUser:
        """Create a new user with encrypted password and return it"""
        return get_user_model().objects.create_user(**validated_data)

    def update(self, instance: AbstractBaseUser, validated_data: Dict[str, Any]) -> AbstractBaseUser:
        """Update a user, set the password correctly and return it"""
        password: str | None = validated_data.pop("password", None)
        user: AbstractBaseUser = super().update(instance, validated_data)
        if password:
            user.set_password(password)
            user.save()

        return user
