from rest_framework.routers import DefaultRouter
from .views import IpamTreeApi

router = DefaultRouter()
router.register('fancytree', IpamTreeApi, basename='ipam-tree')
urlpatterns = router.urls
