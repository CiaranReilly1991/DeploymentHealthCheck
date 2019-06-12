from pyexcel_ods import get_data

data = get_data("/home/kudos/ansible/vars/DSD.ods")
#data = get_data("DSDs/DSD-GMSU.ods")

cluster_personality = data.get("Other")[22][1]
banner = 60
VM_Disk = {}
DSD_Disk = {}
vm_ips = {}
ports = {}
interface_plus_ips = {}
sigtran_interfaces = {}
sum_of_nodes = 1

Int_Names = ['Internal VLAN',
             'External VLAN',
             'SIGTRAN VLAN A',
             'SIGTRAN VLAN B',
             'OAM VLAN',
             'Gy VLAN',
             'Gi VLAN',
             'Backup VLAN']

cluster_types_and_ports = {
    "SMSC": ["2222", "8888", "2775", "29997", "50000", "25", "8090", "2525", "22", "111"],
    "MMSC": ["2222", "8888", "2775", "29997", "50000", "25", "8090", "2525", "22", "111", "8090"],
    "IMX": ["2222", "8888", "2775", "29997", "50000", "25", "8090", "2525", "22", "111", "8088", "8091", "443"],
    "INSIGHT": ["2222", "8888", "2775", "29997", "50000", "25", "8090", "2525", "22", "111", "8087"],
    "INSCARE": ["2222", "8888", "2775", "29997", "50000", "25", "8090", "2525", "22", "111", "8087"]
}


class ReadDSDSpec:
    """
    Class that reads any relavant information from
    the customers DSD.ods file held in the ansible
    container
    """
    def __init__(self):
        """
        Init Method
        """
        self.sum_of_nodes=0

    def read_number_of_nodes(self):
        """
        Gathers the number of nodes for later computing
        :return: Integer
        """
        line = 38
        flag = True

        try:
            isinstance(data.get("Cluster")[line][6], basestring)
        except Exception:
            print "Line indexing out of sync"

        while flag:
            line += 1
            self.sum_of_nodes += 1
            try:
                if "." in data.get("Cluster")[line][1]:
                    # Check for IP sooner than thought
                    flag = False
                else:
                    try:
                        isinstance(data.get("Cluster")[line][1], basestring)
                    except IndexError as error:
                        # Output expected IndexErrors.
                        flag = False
            except IndexError:
                flag = False

        print "Number of Nodes are"
        print self.sum_of_nodes
        return self.sum_of_nodes - 1

    def read_IP_Addresses_from_DSD(self, sum_of_nodes):
        """
        Please do not modify this method :-D
        This method extracts all IP and Network Address information from
        the DSD passed as an argument
        NOTE: This only works with fully fledged DSDs
        :return: Dictionary of IP and Interfaces
        """
        for interfaces in range(38, len(data.get("Cluster"))):
            #print str(data.get("Cluster")[interfaces][0])
            # Check for VIP interfaces and filter out any IPs
            try:
                if "VIP" in str(data.get("Cluster")[interfaces]):
                    continue
            except UnicodeEncodeError:
                continue
            if (data.get("Cluster")[interfaces]) == []:
                continue
            elif str(data.get("Cluster")[interfaces][0]) in Int_Names:
                # Filter for sigtran interfaces for later
                if "SIGTRAN" in str(data.get("Cluster")[interfaces][0]):
                    sigtran_interfaces.update(self.fill_IP_dictionary(interfaces))
                # For all other interfaces with valid IPs,extract and store for later
                elif isinstance(str(data.get("Cluster")[interfaces][1]), str) and not '':
                    if (data.get("Cluster")[interfaces + 1] and data.get("Cluster")[interfaces + 2]) and \
                            (data.get("Cluster")[interfaces + 1][0] or data.get("Cluster")[interfaces + 2][
                                0]) is not '':
                        #print data.get("Cluster")[interfaces]
                        interface_plus_ips.update(self.fill_IP_dictionary(interfaces))
                        if "Backup VLAN" in str(data.get("Cluster")[interfaces][0]):
                            continue
        #print interface_plus_ips
        #print sigtran_interfaces
        return interface_plus_ips, sigtran_interfaces

    def fill_IP_dictionary(self, interfaces):
        """
        Dont ask dictionaries X-F
        :param interface_plus_ips:
        :return: IP addresses from DSD based on size of cluster
        """
        new_list = []
        ips_dict = {}

        new_list.append(str(data.get("Cluster")[interfaces][1]))
        for i in xrange(1, self.sum_of_nodes):
            new_list.append(str(data.get("Cluster")[interfaces+i][0]))

        ips_dict.update(
            {
                str(data.get("Cluster")[interfaces][0]):
                    [
                        new_list
                    ]
            }
        )
        return ips_dict

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
        disk_lines = range(16, len(data.get("OS")))
        for line in disk_lines:
            if "/" in (data.get("OS")[line][0]):
                # This line extracts the Partition and the
                # Size in GB from the OS tab in the DSD
                try:
                    DSD_Disk.update(
                        {
                            str(data.get("OS")[line][0]):
                                str(data.get("OS")[line][4]) + " GB"
                        }
                    )
                except IndexError:
                    continue
            else:
                break
        return DSD_Disk
