from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils.timezone import now, timedelta

from theatre.models import Performance, Play, Reservation, TheatreHall, Ticket

User = get_user_model()


class TheatreModelTests(TestCase):
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

    def test_theatrehall_capacity(self):
        self.assertEqual(self.hall.capacity, 20)

    def test_ticket_not_duplicate(self):
        reservation = Reservation.objects.create(user=self.user)
        ticket = Ticket.objects.create(
            performance=self.performance,
            reservation=reservation, row=1, seat=1
        )
        with self.assertRaises(Exception):
            Ticket.objects.create(
                performance=self.performance,
                reservation=reservation, row=1, seat=1
            )

    def test_ticket_invalid_seat(self):
        reservation = Reservation.objects.create(user=self.user)
        with self.assertRaises(Exception):
            Ticket.objects.create(
                performance=self.performance,
                reservation=reservation, row=1, seat=256
            )
