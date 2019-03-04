import paramiko

banner = 60

cluster_types_and_ports = {
    "SMSC": ["2222", "8888", "2775", "29997", "50000", "25", "8090", "2525", "22", "111"],
    "MMSC": ["2222", "8888", "2775", "29997", "50000", "25", "8090", "2525", "22", "111", "8090"],
    "IMX": ["2222", "8888", "2775", "29997", "50000", "25", "8090", "2525", "22", "111", "8088", "8091", "443"],
    "INSIGHT": ["2222", "8888", "2775", "29997", "50000", "25", "8090", "2525", "22", "111", "8087"],
    "INSCARE": ["2222", "8888", "2775", "29997", "50000", "25", "8090", "2525", "22", "111", "8087"]
}


class Test_DSDVsVM:
    """
    Test Class for comparing expected outputs with VM outputs

    """
    def __init__(self):
        """
        Init Method
        """
        self.username = "centos"
        self.password = "centos"

    def compare_network_ports(self, ports, cluster_personality):
        """
        Compare the network ports gotten from
        each VM and the clusters personality type
        and populate the port_discrepencies
        :return: network_port_diff dictionary
        """
        network_port_diff = {}
        for node_name in ports.keys():
            if cluster_personality in cluster_types_and_ports.keys():
                network_port_diff.update(
                    {
                        node_name: set(cluster_types_and_ports[cluster_personality]) - set(ports[node_name])
                    }
                )
            else:
                print "==" * banner
                print "ERROR: Cluster Personality Not Found"
                print "==" * banner
        return network_port_diff

    def ping_vm_ip_addresses(self, vm_ips, interface_plus_ips):
        """
        This method is responsible for pinging the various
        IP address on different networks between nodes by
        SSH-ing into the different VMs in the cluster
        :return: N/A
        """
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        network_report = {}
        for host_ip, hostname in zip(vm_ips.itervalues(), vm_ips.keys()):
            print "-" * banner
            print "SSH-ing to VM " + hostname + "\n"
            print "-" * banner
            for network, ips in interface_plus_ips.iteritems():
                if "SIGTRAN VLAN " in network:
                    continue
                else:
                    print "*" * banner
                    print "Testing Network " + network + "\n"
                    print "*" * banner
                    for ip in ips:
                        ssh.connect(host_ip, username=self.username, password=self.password, allow_agent=True)
                        _, resp, _ = ssh.exec_command('/usr/bin/ping -c 3 ' + ip)
                        # This line prints all the ping responses
                        print resp.readlines()
                        print "Pinging IP " + ip + " from network " + network + " on node " + host_ip + "\n"
                        try:
                            assert (len(resp.readlines()) < 4)
                        except AssertionError as e:
                            print e
                            network_report[network] = [ip + " IP Not Ping-able from " + hostname]
                            continue
            print "-" * banner
            print hostname + " Completed " + "\n"
            print "-" * banner
            ssh.close()
        return network_report

    def verify_disk_mount_sizes(self, DSD_Disk, VM_Disk):
        """
        Method that compares the DSD Disk partitions
        with the VM disk partitions
        :return: Nothing
        """
        disk_report = {}
        # VM_Disk = TestDisk
        for dsd_partition in DSD_Disk.keys():
            if dsd_partition in VM_Disk.keys():
                # Convert MB to GB for consistency
                if ("M" or "MB") in VM_Disk[dsd_partition]:
                    VM_Disk[dsd_partition] = \
                        str(round
                            (float(
                                VM_Disk[dsd_partition].strip(' M')) * 0.001, 1)) + " GB"
                if (DSD_Disk[dsd_partition].strip('GB') == VM_Disk[dsd_partition].strip('GB')) \
                        or (round(float(DSD_Disk[dsd_partition].strip('GB'))) ==
                            round(float(VM_Disk[dsd_partition].strip('GB')))):
                    print "**" * banner
                    print dsd_partition + " PASS"
                    print "**" * banner
                    continue
                else:
                    disk_report[dsd_partition] = [DSD_Disk[dsd_partition],
                                                  VM_Disk[dsd_partition]]
                    continue
        return disk_report
