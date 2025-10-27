from django.urls import include, path
from rest_framework import routers

from theatre.views import (ActorViewSet, GenreViewSet, PerformanceViewSet,
                           PlayViewSet, ReservationViewSet, TheatreHallViewSet)

app_name = "theatre"

router = routers.DefaultRouter()
router.register("genres", GenreViewSet)
router.register("actors", ActorViewSet)
router.register("theatre_halls", TheatreHallViewSet)
router.register("plays", PlayViewSet)
router.register("performances", PerformanceViewSet)
router.register("reservations", ReservationViewSet)


urlpatterns = router.urls