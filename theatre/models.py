import os
import uuid

from django.contrib.auth.models import User
from django.db import models
from django.core.exceptions import ValidationError
from django.utils.text import slugify


def play_image_file_path(instance, filename):
    _, extension = os.path.splitext(filename)
    filename = f"{slugify(instance.title)}-{uuid.uuid4()}{extension}"

    return os.path.join("uploads/plays/", filename)

class Actor(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)

    class Meta:
        verbose_name = "actor"
        verbose_name_plural = "actors"
        ordering = ("last_name", "first_name")

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"


class Genre(models.Model):
    name = models.CharField(max_length=100)

    class Meta:
        verbose_name = "genre"
        verbose_name_plural = "genres"

    def __str__(self):
        return f"{self.name}"


class Play(models.Model):
    title = models.CharField(max_length=100)
    description = models.TextField()
    actors = models.ManyToManyField(Actor, blank=True, related_name="plays")
    genres = models.ManyToManyField(Genre, blank=True, related_name="plays")
    image = models.ImageField(null=True, blank=True, upload_to=play_image_file_path)
    class Meta:
        verbose_name = "play"
        verbose_name_plural = "plays"

    def __str__(self):
        return f"{self.title}"


class TheatreHall(models.Model):
    name = models.CharField(max_length=100)
    rows = models.IntegerField(null=False, blank=False)
    seats_in_row = models.IntegerField(null=False, blank=False)

    class Meta:
        verbose_name = "theatre hall"
        verbose_name_plural = "theatre halls"

    def __str__(self):
        return f"{self.name}"

    @property
    def capacity(self) -> int:
        return self.rows * self.seats_in_row


class Performance(models.Model):
    show_time = models.DateTimeField()
    play = models.ForeignKey(Play, on_delete=models.CASCADE, related_name="performances")
    theatre_hall = models.ForeignKey(TheatreHall, on_delete=models.CASCADE, related_name="performances")

    class Meta:
        verbose_name = "performance"
        verbose_name_plural = "performances"

    def __str__(self):
        return f"{self.play.title}: Show time: {self.show_time:%Y-%m-%d %H:%M}"


class Reservation(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="reservations")

    class Meta:
        verbose_name = "reservation"
        verbose_name_plural = "reservations"

    def __str__(self):
        return f"{self.user.username}, {self.created_at:%Y-%m-%d %H:%M}"


class Ticket(models.Model):
    row = models.IntegerField()
    seat = models.IntegerField()
    performance = models.ForeignKey(Performance, on_delete=models.CASCADE, related_name="tickets")
    reservation = models.ForeignKey(Reservation, on_delete=models.CASCADE, related_name="tickets")

    @staticmethod
    def validate_ticket(row: int, seat: int, theatre_hall: TheatreHall, error_to_raise):
        for ticket_attr_value, ticket_attr_name, theatre_hall_attr_name in [
            (row, "row", "rows"),
            (seat, "seat", "seats_in_row"),
        ]:
            count_attrs = getattr(theatre_hall, theatre_hall_attr_name)
            if not (1 <= ticket_attr_value <= count_attrs):
                raise error_to_raise(
                    {
                        ticket_attr_name: f"{ticket_attr_name.capitalize()}"
                                          f" must be between 1 and {count_attrs}"
                    }
                )

    def clean(self):
        if Ticket.objects.filter(performance=self.performance, row=self.row, seat=self.seat).exists():
            raise ValidationError({"seat": "This seat is already taken."})
        Ticket.validate_ticket(
            self.row,
            self.seat,
            self.performance.theatre_hall,
            ValidationError
        )

    def save(
            self,
            *args,
            force_insert=False,
            force_update=False,
            using=None,
            update_fields=None
    ):
        self.full_clean()
        return super(Ticket, self).save(
            force_insert,
            force_update,
            using,
            update_fields
        )

    def __str__(self):
        return f"{self.performance.play.title} (row={self.row}, seat={self.seat})"

    class Meta:
        verbose_name = "ticket"
        verbose_name_plural = "tickets"
        ordering = ("row", "seat")
        constraints = [
            models.UniqueConstraint(
                fields=("performance", "row", "seat"),
                name="unique_seat_per_performance"
            )
        ]
