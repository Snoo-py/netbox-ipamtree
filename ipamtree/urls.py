from django.urls import path
from . import views

urlpatterns = [
    path('', views.IpamTreeView.as_view(), name='ipam_tree'),
]
