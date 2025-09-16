from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils.timezone import now
from rest_framework import serializers

from theatre.models import Actor, Genre, Play, TheatreHall, Performance, Reservation, Ticket


class ActorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Actor
        fields = ("id", "first_name", "last_name", "full_name")
        read_only_fields = ("id",)


class GenreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Genre
        fields = ("id", "name")
        read_only_fields = ("id",)

class PlaySerializer(serializers.ModelSerializer):
    genres = serializers.PrimaryKeyRelatedField(many=True, queryset=Genre.objects.all())
    actors = serializers.PrimaryKeyRelatedField(many=True, queryset=Actor.objects.all())
    class Meta:
        model = Play
        fields = ("id", "title", "genres", "actors")

class PlayListSerializer(serializers.ModelSerializer):
        genres = serializers.SlugRelatedField(
            many=True, read_only=True, slug_field="name"
        )
        actors = serializers.SlugRelatedField(
            many=True, read_only=True, slug_field="full_name"
        )

        class Meta:
            model = Play
            fields = ("id", "title", "genres", "actors", "image")

class PlayDetailSerializer(serializers.ModelSerializer):
    genres = GenreSerializer(many=True, read_only=True)
    actors = ActorSerializer(many=True, read_only=True)

    class Meta:
        model = Play
        fields = ("id", "title", "description", "genres", "actors", "image")


class PlayImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Play
        fields = ("id", "image")

class TheatreHallSerializer(serializers.ModelSerializer):
    class Meta:
        model = TheatreHall
        fields = ("id", "name", "rows", "seats_in_row", "capacity")
        read_only_fields = ("id",)


class PerformanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Performance
        fields = ("id", "show_time", "play", "theatre_hall")


class PerformanceListSerializer(serializers.ModelSerializer):
    play_title = serializers.CharField(source="play.title", read_only=True)
    play_image = serializers.ImageField(source="play.image", read_only=True)
    theatre_hall_name = serializers.CharField(source="theatre_hall.name", read_only=True)
    theatre_hall_capacity = serializers.IntegerField(source="theatre_hall.capacity", read_only=True)
    tickets_available = serializers.IntegerField(read_only=True) ###### !!!! Доробити логіку розрахунку залишку квитків

    class Meta:
        model = Performance
        fields = (
            "id",
            "show_time",
            "play_title",
            "play_image",
            "theatre_hall_name",
            "theatre_hall_capacity",
            "tickets_available",
        )


class TicketSerializer(serializers.ModelSerializer):
    def validate(self, attrs):
        attrs = super().validate(attrs)
        performance = attrs["performance"]
        if performance.show_time < now():
            raise serializers.ValidationError("Cannot reserve tickets for past performances!")
        if Ticket.objects.filter(
            performance=attrs["performance"],
            row=attrs["row"],
            seat=attrs["seat"],
        ).exists():
            raise ValidationError({"seat": "This seat is already taken."})
        Ticket.validate_ticket(attrs["row"], attrs["seat"], attrs["performance"].theatre_hall, ValidationError)
        return attrs

    class Meta:
        model = Ticket
        fields = ("id", "row", "seat", "performance")


class TicketListSerializer(serializers.ModelSerializer):
    performance = PerformanceListSerializer(many=False, read_only=True)

    class Meta:
        model = Ticket
        fields = ("id", "row", "seat", "performance")

class TicketSeatsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ticket
        fields = ("row", "seat")


class PerformanceDetailSerializer(PerformanceSerializer):
    play = PlayListSerializer(read_only=True)
    theatre_hall = TheatreHallSerializer(read_only=True)
    taken_places = TicketSeatsSerializer(source="tickets", many=True, read_only=True)

    class Meta:
        model = Performance
        fields = (
            "id",
            "show_time",
            "play",
            "theatre_hall",
            "taken_places",
        )


class ReservationSerializer(serializers.ModelSerializer):
    tickets = TicketSerializer(many=True, read_only=False, write_only=True)
    class Meta:
        model = Reservation
        fields = ("id", "tickets", "created_at")

    def create(self, validated_data):
        with transaction.atomic():
            tickets_data = validated_data.pop("tickets")
            user = self.context["request"].user
            reservation = Reservation.objects.create(user=user, **validated_data)
            for ticket_data in tickets_data:
                Ticket.objects.create(reservation=reservation, **ticket_data)
            return reservation

class ReservationListSerializer(ReservationSerializer):
    tickets = TicketListSerializer(many=True, read_only=True)