from django.views.generic import TemplateView
from django.contrib.auth.mixins import PermissionRequiredMixin

class IpamTreeView(PermissionRequiredMixin, TemplateView):
    permission_required = 'ipam.view_prefix'
    template_name = 'ipamtree/ipamtree.html'

