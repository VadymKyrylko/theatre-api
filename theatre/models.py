from django.contrib.auth.models import User
from django.db import models
from django.core.exceptions import ValidationError


class Actor(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)

    class Meta:
        verbose_name = "actor"
        verbose_name_plural = "actors"
        ordering = ("last_name", "first_name")

    def __str__(self):
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


class Performance(models.Model):
    show_time = models.DateTimeField()
    play = models.ForeignKey(Play, on_delete=models.CASCADE, related_name="performances")
    theatre_hall = models.ForeignKey(TheatreHall, on_delete=models.CASCADE, related_name="performances")

    class Meta:
        verbose_name = "performance"
        verbose_name_plural = "performances"

    def __str__(self):
        return f"{self.play.title}"


class Reservation(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="reservations")

    class Meta:
        verbose_name = "reservation"
        verbose_name_plural = "reservations"

    def __str__(self):
        return f"{self.user.username}"


class Ticket(models.Model):
    row = models.IntegerField()
    seat = models.IntegerField()
    performance = models.ForeignKey(Performance, on_delete=models.CASCADE, related_name="tickets")
    reservation = models.ForeignKey(Reservation, on_delete=models.CASCADE, related_name="tickets")

    class Meta:
        verbose_name = "ticket"
        verbose_name_plural = "tickets"

    def __str__(self):
        return f"{self.performance.play.title} (row={self.row}, seat={self.seat})"

    def clean(self):
        seats_in_row = self.performance.theatre_hall.seats_in_row
        rows = self.performance.theatre_hall.rows
        if self.seat > seats_in_row or self.seat < 1:
            raise ValidationError(f"Seat must be in range 1 - {seats_in_row}!")
        if self.row > rows or self.row < 1:
            raise ValidationError(f"Row must be in range 1 - {rows}!")
        if Ticket.objects.filter(performance=self.performance, row=self.row, seat=self.seat).exists():
            raise ValidationError(f"This seat is already booked!")