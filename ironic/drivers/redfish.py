# Copyright 2017 Red Hat, Inc.
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

from ironic.drivers import generic
from ironic.common import states
from ironic.drivers import base
from ironic.drivers import generic
from ironic.drivers import hardware_type
from ironic.drivers.modules import fake
from ironic.drivers.modules import agent
from ironic.drivers.modules import inspector
from ironic.drivers.modules import ipxe
from ironic.drivers.modules import noop
from ironic.drivers.modules import noop_mgmt
from ironic.drivers.modules import pxe
from ironic.drivers.modules.network import flat as flat_net
from ironic.drivers.modules.network import neutron
from ironic.drivers.modules.network import noop as noop_net
from ironic.drivers.modules.redfish import bios as redfish_bios
from ironic.drivers.modules.redfish import boot as redfish_boot
from ironic.drivers.modules.redfish import inspect as redfish_inspect
from ironic.drivers.modules.redfish import management as redfish_mgmt
from ironic.drivers.modules.redfish import power as redfish_power
from ironic.drivers.modules.redfish import raid as redfish_raid
from ironic.drivers.modules.redfish import vendor as redfish_vendor
from ironic.drivers.modules.storage import noop as noop_storage


class RedfishHardware(generic.GenericHardware):
    """Redfish hardware type."""

    @property
    def supported_bios_interfaces(self):
        """List of supported bios interfaces."""
        return [redfish_bios.RedfishBIOS, noop.NoBIOS]

    @property
    def supported_management_interfaces(self):
        """List of supported management interfaces."""
        return [redfish_mgmt.RedfishManagement, noop_mgmt.NoopManagement]

    @property
    def supported_power_interfaces(self):
        """List of supported power interfaces."""
        return [redfish_power.RedfishPower]

    @property
    def supported_inspect_interfaces(self):
        """List of supported power interfaces."""
        return [redfish_inspect.RedfishInspect, inspector.Inspector,
                noop.NoInspect]

    @property
    def supported_boot_interfaces(self):
        """List of supported boot interfaces."""
        # NOTE(dtantsur): virtual media goes last because of limited hardware
        # vendors support.
        return [ipxe.iPXEBoot, pxe.PXEBoot,
                redfish_boot.RedfishVirtualMediaBoot]

    @property
    def supported_vendor_interfaces(self):
        """List of supported vendor interfaces."""
        return [redfish_vendor.RedfishVendorPassthru, noop.NoVendor]

    @property
    def supported_raid_interfaces(self):
        """List of supported raid interfaces."""
        return [redfish_raid.RedfishRAID, noop.NoRAID, agent.AgentRAID]

class RedfishNetworkAppliance(hardware_type.AbstractHardwareType):
    """Redfish appliance moved between networks and rebooted using Ironic."""

    @property
    def supported_power_interfaces(self):
        return [redfish_power.RedfishPower, fake.FakePower]

    @property
    def supported_inspect_interfaces(self):
        """List of supported power interfaces."""
        # TODO(johng): maybe we only want the port detection?
        return [redfish_inspect.RedfishInspect, noop.NoInspect]

    @property
    def supported_network_interfaces(self):
        """List of supported network interfaces."""
        return [neutron.NeutronNetwork, flat_net.FlatNetwork,
                noop_net.NoopNetwork]

    @property
    def supported_boot_interfaces(self):
        """List of classes of supported boot interfaces."""
        return [fake.FakeBoot]

    @property
    def supported_deploy_interfaces(self):
        """List of supported deploy interfaces."""
        return [NetworkOnlyDeploy]

    @property
    def supported_management_interfaces(self):
        return [noop_mgmt.NoopManagement]

    @property
    def supported_raid_interfaces(self):
        return [noop.NoRAID]

    @property
    def supported_rescue_interfaces(self):
        return [noop.NoRescue]

    @property
    def supported_storage_interfaces(self):
        return [noop_storage.NoopStorage]


class NetworkOnlyDeploy(fake.FakeDeploy):
    """Class for only doing the network part of a typical deployment.
    This does only the network setup,
    then (optionally?) reboots the appliance via redfish,
    letting DHCP do the heavy lifting.
    """

    @base.deploy_step(priority=100)
    def deploy(self, task):
        task.driver.network.configure_tenant_networks(task)
        task.driver.power.reboot(task)

    def tear_down(self, task):
        task.driver.network.unconfigure_tenant_networks(task)
        # TODO(johng): should we power it off?
        task.driver.power.reboot(task)
        return states.DELETED