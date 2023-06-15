from rest_framework.routers import DefaultRouter

from .views import PageViewSet, PagesWriterList  # , PageReaderListViewSet#, PageReaderList

router = DefaultRouter()
router.register('page', PageViewSet, basename='page')
router.register('page-writer-list', PagesWriterList, basename='page-writer-list')
urlpatterns = router.urls
