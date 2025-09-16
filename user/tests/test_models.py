from django.db import IntegrityError
from django.test import TestCase
from django.contrib.auth import get_user_model

User = get_user_model()

class UserModelTests(TestCase):
    def test_create_user(self):
        email = "test@example.com"
        password = "testpass123"
        user = User.objects.create_user(email=email, password=password)

        self.assertEqual(user.email, email)
        self.assertEqual(user.check_password(password), True)

    def test_new_user_email_normalized(self):
        email = "test@EXAMPLE.COM"
        user = User.objects.create_user(email=email, password="test123")
        self.assertEqual(user.email, email.lower())

    def test_create_superuser(self):
        user = User.objects.create_superuser(email="admin@example.com", password="adminpass123")
        self.assertEqual(user.is_superuser, True)
        self.assertEqual(user.is_staff, True)

    def test_user_email_must_be_unique(self):
        email = "unique@example.com"
        User.objects.create_user(email=email, password="testpass123")
        with self.assertRaises(IntegrityError):
            User.objects.create_user(email=email, password="testpass456")