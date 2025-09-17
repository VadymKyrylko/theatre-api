from io import BytesIO

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from django.utils.timezone import now, timedelta
from PIL import Image
from rest_framework import status
from rest_framework.test import APITestCase

from theatre.models import (
    Actor,
    Genre,
    Performance,
    Play,
    Reservation,
    TheatreHall,
    Ticket
)


def generate_test_image():
    file = BytesIO()
    image = Image.new("RGB", (10, 10), color="red")
    image.save(file, "JPEG")
    file.seek(0)
    return SimpleUploadedFile(
        "test.jpg", file.read(), content_type="image/jpeg"
    )


User = get_user_model()


class TheatreViewTests(APITestCase):
    def setUp(self):
        self.password = "testpassword"
        self.user = User.objects.create_user(
            email="test@example.com", password=self.password
        )
        self.staff = User.objects.create_superuser(
            email="admin@example.com", password="adminpass123"
        )
        self.hall = TheatreHall.objects.create(
            name="main", rows=4, seats_in_row=5
        )
        self.genre = Genre.objects.create(name="Drama")
        self.actor = Actor.objects.create(first_name="John", last_name="Smith")
        self.play = Play.objects.create(title="Hamlet", description="Tragedy")
        self.play.genres.add(self.genre)
        self.play.actors.add(self.actor)
        self.performance = Performance.objects.create(
            play=self.play, theatre_hall=self.hall,
            show_time=now() + timedelta(days=1)
        )

        self.token_url = reverse("user:token_obtain_pair")
        self.plays_url = reverse("theatre:play-list")
        self.performances_url = reverse("theatre:performance-list")
        self.reservation_url = reverse("theatre:reservation-list")

        res = self.client.post(
            self.token_url,
            {"email": self.user.email, "password": self.password}
        )
        self.access_token = res.data["access"]

    def authenticate(self, user=None, password=None):
        if not user:
            user = self.user
            password = self.password
        res = self.client.post(
            self.token_url, {"email": user.email, "password": password}
        )
        token = res.data["access"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

    def test_filter_play_by_title(self):
        res = self.client.get(self.plays_url, {"title": "Hamlet"})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["results"][0]["title"], "Hamlet")

    def test_filter_play_by_genre(self):
        res = self.client.get(self.plays_url, {"genres": self.genre.id})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["results"][0]["id"], self.play.id)

    def test_filter_play_by_actor(self):
        res = self.client.get(self.plays_url, {"actors": self.actor.id})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["results"][0]["id"], self.play.id)

    def test_upload_image_only_staff(self):
        url = reverse("theatre:play-upload-image", args=[self.play.id])

        # Regular user
        self.authenticate()
        image = generate_test_image()
        res = self.client.post(url, {"image": image}, format="multipart")
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

        # Staff
        self.authenticate(self.staff, "adminpass123")
        image = generate_test_image()
        res = self.client.post(url, {"image": image}, format="multipart")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn("image", res.data)

    def test_filter_performance_by_date(self):
        date_str = self.performance.show_time.date().isoformat()
        res = self.client.get(self.performances_url, {"date": date_str})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["results"][0]["id"], self.performance.id)

    def test_filter_performance_by_play(self):
        res = self.client.get(self.performances_url, {"play": self.play.id})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["results"][0]["id"], self.performance.id)

    def test_performance_has_tickets_available(self):
        res = self.client.get(self.performances_url)
        self.assertIn("tickets_available", res.data["results"][0])

    def test_user_can_create_reservation(self):
        self.authenticate()
        payload = {
            "tickets": [
                {"performance": self.performance.id, "row": 1, "seat": 1},
            ]
        }
        res = self.client.post(
            self.reservation_url, data=payload, format="json"
        )
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Reservation.objects.filter(user=self.user).count(), 1)

    def test_user_sees_only_own_reservations(self):
        self.authenticate()
        res = self.client.get(self.reservation_url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        for reservation in res.data["results"]:
            self.assertEqual(reservation["user"], self.user.id)

    def test_user_cannot_reserve_past_performance(self):
        past_performance = Performance.objects.create(
            play=self.play, theatre_hall=self.hall,
            show_time=now() - timedelta(days=1)
        )
        self.authenticate()
        payload = {
            "tickets": [
                {"performance": past_performance.id, "row": 1, "seat": 1}
            ]
        }
        res = self.client.post(
            self.reservation_url, data=payload, format="json"
        )
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Reservation.objects.filter(user=self.user).count(), 0)

    def test_user_cannot_reserve_duplicate_ticket(self):
        self.authenticate()
        payload = {
            "tickets": [
                {"performance": self.performance.id, "row": 1, "seat": 1}
            ]
        }
        self.client.post(self.reservation_url, data=payload, format="json")
        res = self.client.post(
            self.reservation_url, data=payload, format="json"
        )
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Reservation.objects.filter(user=self.user).count(), 1)
