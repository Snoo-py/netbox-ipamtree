"""
Creates API endpoint URLs for the plugin.
"""

from netbox.api.routers import NetBoxRouter
from .views import IpamTreeApi

app_name = "ipam-tree"
router = NetBoxRouter()
router.register("fancytree", IpamTreeApi)
urlpatterns = router.urls
