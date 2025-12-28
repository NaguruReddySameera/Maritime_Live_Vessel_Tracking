from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'vessels', views.VesselViewSet, basename='vessel')
router.register(r'positions', views.VesselPositionViewSet, basename='vessel-position')
router.register(r'notes', views.VesselNoteViewSet, basename='vessel-note')
router.register(r'routes', views.VesselRouteViewSet, basename='vessel-route')

urlpatterns = [
    path('', include(router.urls)),
]
