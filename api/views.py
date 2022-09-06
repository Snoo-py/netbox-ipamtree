import netaddr
from rest_framework.response import Response
from rest_framework import viewsets
from ipam.models import Prefix, IPAddress, FHRPGroup


class IpamTreeApi(viewsets.ReadOnlyModelViewSet):
    queryset = Prefix.objects.prefetch_related(
        "site", "vrf__tenant", "tenant", "vlan", "role", "tags"
    )

    def list(self, request):
        networks = self.get_direct_child(netaddr.IPNetwork("0/0"))
        networks += self.get_direct_child(netaddr.IPNetwork("::0/0"))
        data = self.get_fancytree(networks)
        return Response(data)

    def retrieve(self, request, pk=None):
        data = []
        if pk:
            networks = self.get_direct_child(Prefix.objects.get(pk=pk).prefix)
            data = self.get_fancytree(networks)
        return Response(data)

    def add_available_ipaddresses(self, supernet, ips_prefixes, is_pool=False):
        """
        ips_prefixes need to contain only ips and prefixes directly under supernet
        ips_prefixes need to be sorted before.
        """
        output = []
        # Ignore the network and broadcast addresses for non-pool IPv4 prefixes larger than /31.
        if supernet.version == 4 and supernet.prefixlen < 31 and not is_pool:
            first_ip_in_prefix = netaddr.IPAddress(supernet.first)
            last_ip_in_prefix = netaddr.IPAddress(supernet.last - 1)
        else:
            first_ip_in_prefix = netaddr.IPAddress(supernet.first)
            last_ip_in_prefix = netaddr.IPAddress(supernet.last)

        prev_ip = first_ip_in_prefix

        for ip_prefix in ips_prefixes:
            cur_ip = (
                ip_prefix.address.ip
                if isinstance(ip_prefix, IPAddress)
                else ip_prefix.prefix.ip
            )
            diff = int(cur_ip - prev_ip)
            if diff > 1:
                if prev_ip == first_ip_in_prefix:
                    first_skipped = netaddr.IPNetwork(
                        "%s/%s" % (prev_ip, supernet.prefixlen)
                    )
                else:
                    first_skipped = netaddr.IPNetwork(
                        "%s/%s" % (prev_ip + 1, supernet.prefixlen)
                    )
                skipped_count = diff - 1
                output.append((skipped_count, first_skipped))
            output.append(ip_prefix)
            prev_ip = (
                ip_prefix.address.ip
                if isinstance(ip_prefix, IPAddress)
                else netaddr.IPAddress(ip_prefix.prefix.last)
            )

        # Include any remaining available IPs
        if prev_ip < last_ip_in_prefix:
            skipped_count = int(last_ip_in_prefix - prev_ip)
            first_skipped = netaddr.IPNetwork(
                "%s/%s" % (prev_ip + 1, supernet.prefixlen)
            )
            output.append((skipped_count, first_skipped))
        return output

    def get_direct_child(self, supernet, vrf=None):
        supernet_depth = -1
        if supernet not in [netaddr.IPNetwork("0/0"), netaddr.IPNetwork("::0/0")]:
            supernet_prefix = Prefix.objects.get(prefix=str(supernet))
            supernet_depth = supernet_prefix.depth

        prefixes = Prefix.objects.filter(
            prefix__net_contained=str(supernet), _depth=(supernet_depth + 1)
        )

        for prefix in prefixes:
            prefix.t_has_child = prefix.children > 0

        ips = []
        for ip in IPAddress.objects.filter(address__net_host_contained=str(supernet)):
            for prefix in prefixes:
                # Need to specify ip.address.ip and not just ip.address to check just the ip and not ip+cidr.
                if ip.address.ip in prefix.prefix:
                    prefix.t_has_child = True
                    break
            else:
                ips.append(ip)

        child_nets = sorted(
            set(prefixes) | set(ips),
            key=lambda i: i.address.ip if isinstance(i, IPAddress) else i.prefix.ip,
        )
        if supernet not in [netaddr.IPNetwork("0/0"), netaddr.IPNetwork("::0/0")]:
            child_nets = self.add_available_ipaddresses(supernet, child_nets)
        return child_nets

    def get_fancytree(self, networks):
        data = []
        for s in networks:
            if isinstance(s, tuple):
                tmp = {
                    "title": '<span class="badge bg-success">%s IPs available</a>'
                    % (s[0]),
                    "key": -1,
                    "netbox": {
                        "free_ips": True,
                    },
                }
                data.append(tmp)
                continue
            prefix = False
            if isinstance(s, Prefix):
                prefix = True
            device = None
            device_url = None
            if not prefix:
                assigned_object = s.assigned_object
                if isinstance(assigned_object, FHRPGroup):
                    device = assigned_object.description
                    device_url = assigned_object.get_absolute_url()
                elif assigned_object:
                    device = assigned_object.parent_object
                    device_url = device.get_absolute_url() if device else None
                    device = str(device)
            tmp = {
                "title": '<a href="%s">%s</a>'
                % (s.get_absolute_url(), str(s.prefix) if prefix else str(s.address)),
                "key": s.id,
                "lazy": s.t_has_child > 0 if prefix else False,
                "folder": True if prefix else False,
                "netbox": {
                    "prefix": prefix,
                    "status": s.get_status_display(),
                    "status_color": s.get_status_color(),
                    "role": s.get_role_display() if not prefix else None,
                    "role_color": s.get_role_color() if not prefix else None,
                    "utilization": round(s.get_utilization()) if prefix else None,
                    "vlan": str(s.vlan) if prefix else None,
                    "site": str(s.site) if prefix else None,
                    "description": s.description,
                    "device": device,
                    "device_url": device_url,
                },
            }
            data.append(tmp)
        return data
