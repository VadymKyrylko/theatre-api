from datetime import datetime
from typing import List, Type, Any

from django.db.models import Count, F, QuerySet
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import mixins, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAdminUser
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import BaseSerializer

from theatre.models import (Actor, Genre, Performance, Play, Reservation,
                            TheatreHall)
from theatre.serializers import (ActorSerializer, GenreSerializer,
                                 PerformanceDetailSerializer,
                                 PerformanceListSerializer,
                                 PerformanceSerializer, PlayDetailSerializer,
                                 PlayImageSerializer, PlayListSerializer,
                                 PlaySerializer, ReservationListSerializer,
                                 ReservationSerializer, TheatreHallSerializer)


class GenreViewSet(
    mixins.CreateModelMixin, mixins.ListModelMixin, viewsets.GenericViewSet
):
    queryset = Genre.objects.all()
    serializer_class = GenreSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)


class ActorViewSet(
    mixins.CreateModelMixin, mixins.ListModelMixin, viewsets.GenericViewSet
):
    queryset = Actor.objects.all()
    serializer_class = ActorSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)


class TheatreHallViewSet(
    mixins.CreateModelMixin, mixins.ListModelMixin, viewsets.GenericViewSet
):
    queryset = TheatreHall.objects.all()
    serializer_class = TheatreHallSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)


class PlayViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    queryset = (Play.objects.prefetch_related(
        "genres", "actors")
                .order_by("title"))
    serializer_class = PlaySerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)

    @staticmethod
    def _params_to_ints(queryset: str) -> List[int]:
        """Convert a list of string IDs to a list of integers."""
        return [int(str_id) for str_id in queryset.split(",")]

    def get_queryset(self) -> QuerySet[Play]:
        """Retrieve the plays with filters."""
        title: str | None = self.request.query_params.get("title")
        genres: str | None = self.request.query_params.get("genres")
        actors:  str | None = self.request.query_params.get("actors")

        queryset: QuerySet[Play] = self.queryset
        if title:
            queryset = queryset.filter(title__icontains=title)
        if genres:
            genres_ids = self._params_to_ints(genres)
            queryset = queryset.filter(genres__id__in=genres_ids)
        if actors:
            actors_ids = self._params_to_ints(actors)
            queryset = queryset.filter(actors__id__in=actors_ids)
        return queryset.distinct()

    def get_serializer_class(self) -> Type[BaseSerializer]:
        if self.action == "list":
            return PlayListSerializer
        if self.action == "retrieve":
            return PlayDetailSerializer
        if self.action == "upload_image":
            return PlayImageSerializer
        return PlaySerializer

    @action(
        methods=["POST"],
        detail=True,
        url_path="upload-image",
        permission_classes=[IsAdminUser],
    )
    def upload_image(self, request: Request, pk: int | None = None) -> Response:
        """Endpoint for uploading an image to specific play"""
        play = self.get_object()
        serializer = self.get_serializer(play, data=request.data)

        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                "genres",
                type={"type": "list", "items": {"type": "number"}},
                description="Filter by genre id (ex. ?genres=2,5)",
            ),
            OpenApiParameter(
                "actors",
                type={"type": "list", "items": {"type": "number"}},
                description="Filter by actor id (ex. ?actors=2,5)",
            ),
            OpenApiParameter(
                "title",
                type=OpenApiTypes.STR,
                description="Filter by play title (ex. ?title=love)",
            ),
        ]
    )
    def list(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        return super().list(request, *args, **kwargs)


class PerformanceViewSet(viewsets.ModelViewSet):
    queryset = (
        Performance.objects.all()
        .select_related("play", "theatre_hall")
        .annotate(
            tickets_available=(
                F("theatre_hall__rows") * F("theatre_hall__seats_in_row")
                - Count("tickets")
            )
        )
        .order_by("-show_time")
    )
    serializer_class = PerformanceSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)

    def get_queryset(self) -> QuerySet[Performance]:
        date: str | None = self.request.query_params.get("date")
        play_id_str: str | None = self.request.query_params.get("play")

        queryset: QuerySet[Performance] = self.queryset

        if date:
            try:
                date = datetime.strptime(date, "%Y-%m-%d").date()
            except ValueError:
                raise ValidationError("Invalid date format. Use YYYY-MM-DD.")
            queryset = queryset.filter(show_time__date=date)

        if play_id_str:
            try:
                play_id = int(play_id_str)
            except ValueError:
                raise ValidationError("Invalid play ID. Must be an integer.")
            queryset = queryset.filter(play_id=int(play_id_str))
        return queryset

    def get_serializer_class(self) -> Type[BaseSerializer]:
        if self.action == "list":
            return PerformanceListSerializer
        if self.action == "retrieve":
            return PerformanceDetailSerializer
        return PerformanceSerializer

    @extend_schema(
        parameters=[
            OpenApiParameter(
                "play",
                type=OpenApiTypes.INT,
                description="Filter by play id (ex. ?play=2)",
            ),
            OpenApiParameter(
                "date",
                type=OpenApiTypes.DATE,
                description="Filter by datetime of Performance "
                            "(ex. ?date=2025-09-08)",
            ),
        ]
    )
    def list(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        return super().list(request, *args, **kwargs)


class ReservationPagination(PageNumberPagination):
    page_size = 10
    max_page_size = 30
    page_size_query_param = "page_size"


class ReservationViewSet(
    mixins.CreateModelMixin, mixins.ListModelMixin, viewsets.GenericViewSet
):
    queryset = Reservation.objects.prefetch_related(
        "tickets__performance__play", "tickets__performance__theatre_hall"
    ).order_by("-created_at")
    serializer_class = ReservationSerializer
    pagination_class = ReservationPagination
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self) -> QuerySet[Reservation]:
        return self.queryset.filter(user=self.request.user)

    def get_serializer_class(self) -> Type[BaseSerializer]:
        if self.action == "list":
            return ReservationListSerializer
        return ReservationSerializer

    def perform_create(self, serializer: BaseSerializer) -> None:
        serializer.save()
