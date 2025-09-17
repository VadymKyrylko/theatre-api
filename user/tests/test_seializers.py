from django.contrib.auth import get_user_model
from django.test import TestCase

from user.serializers import UserSerializer

User = get_user_model()


class UserSerializerTests(TestCase):
    def setUp(self):
        self.password = "testpass123"
        self.user = User.objects.create_user(
            email="test@example.com",
            password=self.password,
        )

    def test_create_user_successful(self):
        data = {"email": "new@example.com", "password": "newtestpass123"}
        serializer = UserSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        user = serializer.save()
        self.assertEqual(user.email, data["email"])
        self.assertTrue(user.check_password(data["password"]))
        self.assertFalse(user.is_staff)

    def test_password_is_write_only(self):
        serializer = UserSerializer(self.user)
        self.assertNotIn("password", serializer.data)

    def test_password_min_length(self):
        data = {"email": "new@example.com", "password": "123"}
        serializer = UserSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("password", serializer.errors)

    def test_update_user_password(self):
        data = {"email": "update@example.com", "password": "newpass123"}
        serializer = UserSerializer(self.user, data=data, partial=True)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        updated_user = serializer.save()
        self.assertEqual(updated_user.email, data["email"])
        self.assertTrue(updated_user.check_password(data["password"]))

    def test_is_staff_read_only(self):
        data = {
            "email": "staff@example.com",
            "password": "pass123",
            "is_staff": True
        }
        serializer = UserSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        user = serializer.save()
        self.assertFalse(user.is_staff)
