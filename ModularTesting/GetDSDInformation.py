from pyexcel_ods import get_data
import json
import pdb

data = get_data("/home/kudos/ansible/vars/DSD.ods")
#data = get_data("../DSD_Du_MMSC_S2.ods")

cluster_personality = data.get("Other")[22][1]
banner = 60
VM_Disk = {}
DSD_Disk = {}
vm_ips = {}
ports = {}
interface_plus_ips = {}
Int_Names = ['Internal VLAN',
             'Internal VLAN VIP',
             'External VLAN',
             'External VLAN VIP',
             'SIGTRAN VLAN A',
             'SIGTRAN VLAN B',
             'OAM VLAN',
             'OAM VLAN VIP',
             'Gy VLAN',
             'Gy VLAN VIP',
             'Gi VLAN',
             'Gi VLAN VIP',
             'Backup VLAN']


class ReadDSDSpec:
    """
    Class that reads any relavant information from
    the customers DSD.ods file held in the ansible
    container
    """
    def __init__(self):
        """

        """

    def read_IP_Addresses_from_DSD(self):
        """
        Please do not modify this method :-D
        This method extracts all IP and Network Address information from
        the DSD passed as an argument
        NOTE: This only works with fully fledged DSDs
        :return: Dictionary of IP and Interfaces
        """
        for interfaces in range(38, len(data.get("Cluster"))):
            if (data.get("Cluster")[interfaces]) == []:
                continue
            elif str(data.get("Cluster")[interfaces][0]) in Int_Names:
                if "VIP" in str(data.get("Cluster")[interfaces][0]):
                    if len(data.get("Cluster")[interfaces]) is not 1 \
                            and isinstance(str(data.get("Cluster")[interfaces][1]), str):
                        interface_plus_ips.update(
                            {
                                str(data.get("Cluster")[interfaces][0])
                                :
                                    [
                                        str(data.get("Cluster")[interfaces][1])
                                    ]
                            }
                        )
                    else:
                        continue
                elif isinstance(str(data.get("Cluster")[interfaces][1]), str) and not '':
                    if (data.get("Cluster")[interfaces + 1] and data.get("Cluster")[interfaces + 2]) and \
                            (data.get("Cluster")[interfaces + 1][0] or data.get("Cluster")[interfaces + 2][
                                0]) is not '':
                        interface_plus_ips.update(
                            {
                                str(data.get("Cluster")[interfaces][0]):
                                    [
                                        str(data.get("Cluster")[interfaces][1]),
                                        str(data.get("Cluster")[interfaces + 1][0]),
                                        str(data.get("Cluster")[interfaces + 2][0])
                                    ]
                            }
                        )
        return interface_plus_ips
        #print interface_plus_ips

    def read_disk_partitions_from_DSD(self):
        """
        Method: read_disk_partitions_from_DSD
        Purpose: To read disk partitions from DSD
        Comments:

        DSD is currently set above, but we will
        eventually pass the DSD as an arguement
        when running the scripts. I've tested
        with a few DSD's and seems to work fine.

        """
        disk_lines = range(15, len(data.get("OS")))
        for line in disk_lines:
            if "/" in (data.get("OS")[line][0]):
                # This line extracts the Partition and the
                # Size in GB from the OS tab in the DSD
                DSD_Disk.update(
                    {
                        str(data.get("OS")[line][0]):
                            str(data.get("OS")[line][4]) + " GB"
                    }
                )
            else:
                break
        return DSD_Disk
