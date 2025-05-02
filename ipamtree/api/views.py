import netaddr
from rest_framework.response import Response
from rest_framework import viewsets

# from ipam.views import add_available_ipaddresses
from ipam.models import Prefix, IPAddress, FHRPGroup


class FancyObj(object):
    @property
    def fancy_url(self):
        pass

    @property
    def fancy_text(self):
        pass

    @property
    def fancy_id(self):
        pass

    @property
    def fancy_lazy(self):
        return False

    @property
    def fancy_folder(self):
        return False

    @property
    def fancy_prefix(self):
        return False

    @property
    def fancy_status(self):
        pass

    @property
    def fancy_status_color(self):
        pass

    @property
    def fancy_role(self):
        return None

    @property
    def fancy_role_color(self):
        return None

    @property
    def fancy_utilization(self):
        return None

    @property
    def fancy_vlan(self):
        return None

    @property
    def fancy_site(self):
        return None

    @property
    def fancy_description(self):
        pass

    @property
    def fancy_device(self):
        return None

    @property
    def fancy_device_url(self):
        return None

    def get_fancy_obj(self):
        return {
            "title": f'<a href="{self.fancy_url}">{self.fancy_text}</a>',
            "key": self.fancy_id,
            "lazy": self.fancy_lazy,
            "folder": self.fancy_folder,
            "netbox": {
                "prefix": self.fancy_prefix,
                "status": self.fancy_status,
                "status_color": self.fancy_status_color,
                "role": self.fancy_role,
                "role_color": self.fancy_role_color,
                "utilization": self.fancy_utilization,
                "vlan": self.fancy_vlan,
                "site": self.fancy_site,
                "description": self.fancy_description,
                "device": self.fancy_device,
                "device_url": self.fancy_device_url,
            },
        }


class FancyIp(IPAddress, FancyObj):
    class Meta:
        proxy = True

    @property
    def fc_net(self):
        return netaddr.IPNetwork(f"{str(self.address.ip)}/32")

    @property
    def fc_net_first(self):
        return self.address.ip

    @property
    def fc_net_last(self):
        return self.address.ip

    @property
    def fancy_url(self):
        return f"/ipam/ip-addresses/{self.pk}"

    @property
    def fancy_text(self):
        return str(self.address)

    @property
    def fancy_id(self):
        return self.id

    @property
    def fancy_status(self):
        return self.get_status_display()

    @property
    def fancy_status_color(self):
        return self.get_status_color()

    @property
    def fancy_role(self):
        return self.get_role_display()

    @property
    def fancy_role_color(self):
        return self.get_role_color()

    @property
    def fancy_description(self):
        return self.description

    @property
    def fancy_device(self):
        assigned_object = self.assigned_object
        if isinstance(assigned_object, FHRPGroup):
            return assigned_object.description
        elif assigned_object:
            return str(assigned_object.parent_object)
        return None

    @property
    def fancy_device_url(self):
        assigned_object = self.assigned_object
        if isinstance(assigned_object, FHRPGroup):
            return f"/ipam/fhrp-groups/{assigned_object.pk}"
        elif assigned_object:
            device = assigned_object.parent_object
            return f"/dcim/devices/{device.pk}" if device else None
        return None


class FancyPrefix(Prefix, FancyObj):
    class Meta:
        proxy = True

    @property
    def fc_net(self):
        return self.prefix

    @property
    def fc_net_first(self):
        return netaddr.IPAddress(self.prefix.first)

    @property
    def fc_net_last(self):
        return netaddr.IPAddress(self.prefix.last)

    @property
    def fancy_url(self):
        if self.status:
            return f"/ipam/prefixes/{self.pk}"
        return ""

    @property
    def fancy_text(self):
        return str(self.prefix)

    @property
    def fancy_id(self):
        return self.id

    @property
    def fancy_lazy(self):
        if self.status:
            return True
        return False

    @property
    def fancy_folder(self):
        return True

    @property
    def fancy_prefix(self):
        return True

    @property
    def fancy_status(self):
        if self.status:
            return self.get_status_display()
        return "Available"

    @property
    def fancy_status_color(self):
        if self.status:
            return self.get_status_color()
        return "success"

    @property
    def fancy_utilization(self):
        if self.status:
            return round(self.get_utilization())
        return None

    @property
    def fancy_vlan(self):
        return str(self.vlan)

    @property
    def fancy_site(self):
        return str(self.scope)

    @property
    def fancy_description(self):
        return self.description


class FancyFreeIPs(netaddr.IPNetwork):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._free_ips_count = 0

    @property
    def fc_net(self):
        return self

    def set_free_ips(self, value):
        self._free_ips_count = value

    def get_fancy_obj(self):
        txt = self._free_ips_count
        if txt > 65536:
            txt = "Many"
        return {
            "title": f'<span class="badge bg-success">{txt} IPs available</a>',
            "key": -1,
            "netbox": {
                "free_ips": True,
            },
        }


class FancyTreeNetwork(object):
    def __init__(self, pk=None, network=None):
        self._netbox_prefix = None
        self._network = network
        if pk:
            self._netbox_prefix = FancyPrefix.objects.get(pk=pk)
            self._network = self._netbox_prefix.prefix
        self._children_prefixes = None

    @property
    def netbox_prefix(self):
        return self._netbox_prefix

    @property
    def network(self):
        return self._network

    @property
    def is_top_network(self):
        return self.network in [
            netaddr.IPNetwork("0.0.0.0/0"),
            netaddr.IPNetwork("::0/0"),
        ]

    @property
    def children_network_depth(self):
        if self.netbox_prefix:
            return self.netbox_prefix.depth + 1
        return 0

    @property
    def child_prefixes(self):
        if self._children_prefixes == None:
            self._children_prefixes = FancyPrefix.objects.filter(
                prefix__net_contained=str(self.network),
                _depth=self.children_network_depth,
            )
        return self._children_prefixes

    @property
    def child_ips(self):
        return FancyIp.objects.filter(address__net_contains_or_equals=str(self.network))

    @property
    def first_ip_in_prefix(self):
        if self.network.version == 6 or (
            self.network.version == 4 and self.network.prefixlen == 31
        ):
            return netaddr.IPAddress(self.network.first)
        else:
            return netaddr.IPAddress(self.network.first + 1)

    @property
    def last_ip_in_prefix(self):
        if self.network.version == 4 and self.network.prefixlen == 31:
            return netaddr.IPAddress(self.network.last)
        else:
            return netaddr.IPAddress(self.network.last - 1)

    def get_available_child_prefixes(self):
        """
        Return maximum prefix size available.
        """
        if not self.child_prefixes:
            return []
        available_prefixes = netaddr.IPSet(self.network) ^ netaddr.IPSet(
            [p.prefix for p in self.child_prefixes]
        )
        available_prefixes = [
            FancyPrefix(prefix=p, status=None) for p in available_prefixes.iter_cidrs()
        ]
        available_prefixes = sorted(available_prefixes, key=lambda p: p.mask_length)
        clean_prefixes = []
        for pr in available_prefixes:
            for cl_pr in clean_prefixes:
                if pr.prefix in cl_pr.prefix:
                    break
            clean_prefixes.append(pr)
        return clean_prefixes

    def get_available_ipaddresses(self, child_nets, is_pool=False):
        """
        Return number of available IPs between allocate IPs and Prefix.
        """
        output = []
        start_ip = self.first_ip_in_prefix

        for child_net in sorted(child_nets, key=lambda i: i.fc_net.ip):
            if start_ip in child_net.fc_net:
                start_ip = netaddr.IPAddress(child_net.fc_net_last + 1)
                continue
            end_ip = child_net.fc_net_first - 1
            free_ips = FancyFreeIPs(f"{start_ip}/{self.network.prefixlen}")
            free_ips.set_free_ips(int(end_ip - start_ip + 1))
            output.append(free_ips)
            start_ip = netaddr.IPAddress(child_net.fc_net_last + 1)

        # Include any remaining available IPs
        if start_ip < self.last_ip_in_prefix:
            end_ip = self.last_ip_in_prefix
            free_ips = FancyFreeIPs(f"{start_ip}/{self.network.prefixlen}")
            free_ips.set_free_ips(int(end_ip - start_ip + 1))
            output.append(free_ips)
        return output

    def get_children(self):
        child_nets = list(set(self.child_prefixes) | set(self.child_ips))
        if not self.is_top_network and self.netbox_prefix.status == "container":
            child_nets += self.get_available_child_prefixes()
        elif not self.is_top_network:
            child_nets += self.get_available_ipaddresses(child_nets)

        child_nets = sorted(child_nets, key=lambda i: i.fc_net.ip)
        return child_nets


class IpamTreeApi(viewsets.ReadOnlyModelViewSet):
    queryset = Prefix.objects.prefetch_related(
        "site", "vrf__tenant", "tenant", "vlan", "role", "tags"
    )

    def list(self, request):
        networks = FancyTreeNetwork(
            network=netaddr.IPNetwork("0.0.0.0/0")
        ).get_children()
        networks += FancyTreeNetwork(network=netaddr.IPNetwork("::0/0")).get_children()
        data = self.get_fancytree(networks)
        return Response(data)

    def retrieve(self, request, pk=None):
        data = []
        if pk:
            net = FancyTreeNetwork(pk=pk)
            networks = net.get_children()
            data = self.get_fancytree(networks)
        return Response(data)

    def get_fancytree(self, networks):
        data = []
        for s in networks:
            data.append(s.get_fancy_obj())
        return data
