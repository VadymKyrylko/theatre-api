from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils.timezone import now, timedelta

from theatre.models import Performance, Play, TheatreHall
from theatre.serializers import ReservationSerializer

User = get_user_model()


class TheatreSerializerTests(TestCase):
    def setUp(self):
        self.hall = TheatreHall.objects.create(
            name="main", rows=4, seats_in_row=5
        )
        self.play = Play.objects.create(
            title="Some play", description="Some description"
        )
        self.performance = Performance.objects.create(
            play=self.play, theatre_hall=self.hall,
            show_time=now() + timedelta(days=1)
        )
        self.user = User.objects.create(
            email="test@example.com", password="testpassword"
        )

    def test_create_reservation_with_tickets(self):
        data = {
            "tickets": [
                {"performance": self.performance.id, "row": 1, "seat": 1},
                {"performance": self.performance.id, "row": 1, "seat": 2},
            ]
        }
        serializer = ReservationSerializer(
            data=data, context={
                "request": type("object", (), {"user": self.user})
            }
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
        reservation = serializer.save()
        self.assertEqual(reservation.tickets.count(), 2)
