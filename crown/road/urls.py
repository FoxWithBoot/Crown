from rest_framework.routers import DefaultRouter

from .views import RoadViewSet

router = DefaultRouter()
router.register('road', RoadViewSet, basename='road')
urlpatterns = router.urls
