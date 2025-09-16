from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model

User = get_user_model()

class UserViewsTests(APITestCase):
    def setUp(self):
        self.password = "testpass123"
        self.user = User.objects.create(
            email="test@example.com",
            password=self.password,
        )
        self.register_url = reverse("user:create")
        self.me_url = reverse("user:manage")

    def test_register_user_successful(self):
        payload = {"email": "new@example.com", "password": "newpass123"}
        res = self.client.post(self.register_url, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(email=payload["email"]).exists())

    def test_register_user_invalid_password(self):
        payload = {"email": "short@example.com", "password": "123"}
        res = self.client.post(self.register_url, payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_user_duplicate_email(self):
        payload = {"email": self.user.email, "password": "password1"}
        res = self.client.post(self.register_url, payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_manage_user_unauthorized(self):
        res = self.client.get(self.me_url)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_manage_user_retrieve_authorized(self):
        self.client.force_authenticate(user=self.user)
        res = self.client.get(self.me_url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["email"], self.user.email)

    def test_manage_user_update_email(self):
        self.client.force_authenticate(user=self.user)
        payload = {"email": "updated@example.com"}
        res = self.client.patch(self.me_url, payload)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, payload["email"])

    def test_manage_user_update_password(self):
        self.client.force_authenticate(user=self.user)
        payload = {"password": "newpass123"}
        res = self.client.patch(self.me_url, payload)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password(payload["password"]))
