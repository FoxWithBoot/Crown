from rest_framework.routers import DefaultRouter

from .views import PageViewSet, PageWriterList, PageReaderList

router = DefaultRouter()
router.register('page', PageViewSet, basename='page')
router.register('page-writer-list', PageWriterList, basename='page-writer-list')
router.register('page-reader-list', PageReaderList, basename='page-reader-list')
urlpatterns = router.urls
