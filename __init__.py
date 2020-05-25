from extras.plugins import PluginConfig

class IpamTreeConfig(PluginConfig):
    name = 'ipamtree'
    verbose_name = 'Ipam Tree'
    description = 'Ipam tree display for netbox'
    version = '0.1'
    base_url = 'ipam-tree'
    required_settings = []

config = IpamTreeConfig
