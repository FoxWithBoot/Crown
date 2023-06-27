from rest_framework.routers import DefaultRouter

from .views import BlockViewSet

router = DefaultRouter()
router.register('blocks', BlockViewSet, basename='blocks')
urlpatterns = router.urls
