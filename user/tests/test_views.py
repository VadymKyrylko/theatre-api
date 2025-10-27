from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

User = get_user_model()


class UserApiTests(APITestCase):
    def setUp(self):
        self.password = "testpass123"
        self.user = User.objects.create_user(
            email="test@example.com", password=self.password
        )
        self.register_url = reverse("user:create")
        self.me_url = reverse("user:manage")
        self.token_url = reverse("user:token_obtain_pair")

    def authenticate_user(self):
        res = self.client.post(
            self.token_url,
            {"email": self.user.email, "password": self.password}
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        token = res.data["access"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

    def test_register_user_successful(self):
        payload = {"email": "new@example.com", "password": "newpass123"}
        res = self.client.post(self.register_url, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

    def test_register_user_short_password(self):
        payload = {"email": "short@example.com", "password": "123"}
        res = self.client.post(self.register_url, payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_user_duplicate_email(self):
        payload = {"email": self.user.email, "password": "password123"}
        res = self.client.post(self.register_url, payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_token_obtain_success(self):
        res = self.client.post(
            self.token_url,
            {"email": self.user.email, "password": self.password}
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn("access", res.data)

    def test_token_obtain_invalid_credentials(self):
        res = self.client.post(
            self.token_url, {"email": self.user.email, "password": "wrongpass"}
        )
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_manage_user_unauthorized(self):
        res = self.client.get(self.me_url)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_manage_user_authorized(self):
        self.authenticate_user()
        res = self.client.get(self.me_url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["email"], self.user.email)

    def test_manage_user_update_email(self):
        self.authenticate_user()
        payload = {"email": "updated@example.com"}
        res = self.client.patch(self.me_url, payload)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, payload["email"])

    def test_manage_user_update_password(self):
        self.authenticate_user()
        payload = {"password": "newpass123"}
        res = self.client.patch(self.me_url, payload)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(self.user.check_password(payload["password"]), True)
