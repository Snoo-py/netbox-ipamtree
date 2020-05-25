import netaddr
from rest_framework.response import Response
from rest_framework import viewsets
from ipam.models import Prefix, IPAddress



class IpamTreeApi(viewsets.ReadOnlyModelViewSet):
    queryset =  Prefix.objects.prefetch_related('site', 'vrf__tenant', 'tenant', 'vlan', 'role', 'tags')


    def list(self, request):
        networks = self.get_direct_child()
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
            cur_ip = ip_prefix.address.ip if isinstance(ip_prefix, IPAddress) else ip_prefix.prefix.ip
            diff = int(cur_ip - prev_ip)
            if diff > 1:
                if prev_ip == first_ip_in_prefix:
                    first_skipped = netaddr.IPNetwork('%s/%s' % (prev_ip, supernet.prefixlen))
                else:
                    first_skipped = netaddr.IPNetwork('%s/%s' % (prev_ip + 1, supernet.prefixlen))
                skipped_count = diff - 1
                output.append((skipped_count, first_skipped))
            output.append(ip_prefix)
            prev_ip = ip_prefix.address.ip if isinstance(ip_prefix, IPAddress) else netaddr.IPAddress(ip_prefix.prefix.last)

        # Include any remaining available IPs
        if prev_ip < last_ip_in_prefix:
            skipped_count = int(last_ip_in_prefix - prev_ip)
            first_skipped = netaddr.IPNetwork('%s/%s' % (prev_ip + 1, supernet.prefixlen))
            output.append((skipped_count, first_skipped))
        return output


    def get_direct_child(self, supernet=netaddr.IPNetwork('0.0.0.0/0'), vrf=None):
        child_nets = []
        prefixes = Prefix.objects.filter(prefix__net_contained=str(supernet))
        ips = set(IPAddress.objects.filter(address__net_host_contained=str(supernet)))

        for prefix in prefixes:
            if prefix.prefix == supernet:
                continue

            # Remove child ips of prefix p to just keep ip directly under supernet
            has_child = False
            ips_to_remove = set()
            for ip in ips:
                if ip.address.ip in prefix.prefix:
                    ips_to_remove.add(ip)
                    has_child = True
            prefix.t_has_child = has_child
            ips = ips - ips_to_remove

            # Keep only subnet directly under supernet
            for child_net in child_nets:
                if prefix.prefix == child_net.prefix:
                    break
                if prefix.prefix in child_net.prefix:
                    child_net.t_has_child = True
                    break
                if child_net.prefix in prefix.prefix:
                    child_nets.remove(child_net)
                    prefix.t_has_child = True
            else:
                child_nets.append(prefix)

        child_nets = sorted(set(child_nets) | set(ips), key=lambda i: i.address.ip if isinstance(i, IPAddress) else i.prefix.ip)
        if supernet != netaddr.IPNetwork('0.0.0.0/0'):
            child_nets = self.add_available_ipaddresses(supernet, child_nets)
        return child_nets


    def get_fancytree(self, networks):
        data = []
        for s in networks:
            if isinstance(s, tuple):
                tmp = {
                    'title': '<span class="label label-success">%s IPs available</a>' % (s[0]),
                    'key': -1,
                    'netbox': {
                        'free_ips': True,
                    }
                }
                data.append(tmp)
                continue
            prefix = False
            if isinstance(s, Prefix):
                prefix = True
            device = None
            device_url = None
            if not prefix:
                device = s.assigned_object.device or s.assigned_object.virtual_machine if s.assigned_object else None
                device_url = device.get_absolute_url() if device else None
                device = str(device)
            tmp = {
                'title': '<a href="%s">%s</a>' % (s.get_absolute_url(), str(s.prefix) if prefix else str(s.address)),
                'key': s.id,
                'lazy': s.__dict__.get('t_has_child', False),
                'folder': True if prefix else False,
                'netbox': {
                    'prefix': prefix,
                    'status': s.get_status_display(),
                    'status_class': s.get_status_class(),
                    'utilization': s.get_utilization() if prefix else None,
                    'vlan': str(s.vlan) if prefix else None,
                    'site': str(s.site) if prefix else None,
                    'description': s.description,
                    'device': device,
                    'device_url': device_url,
                }
            }
            data.append(tmp)
        return data

