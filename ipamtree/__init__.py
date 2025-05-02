from netbox.plugins import PluginConfig

from ipamtree.version import __version__


class IpamTreeConfig(PluginConfig):
    # Basic plugin identification
    name = "ipamtree"
    verbose_name = "IPAM Tree"
    description = "Ipam tree display for netbox"
    version = __version__

    # URL and integration settings
    base_url = "ipam-tree"

    # Compatibility information
    min_version = "4.2.0"
    max_version = "4.2.99"
    required_settings = []


config = IpamTreeConfig
