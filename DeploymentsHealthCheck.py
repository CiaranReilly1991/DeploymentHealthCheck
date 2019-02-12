"""
This python script allows us to test several node configs before
deploying TC6000

Currently the script requires the DSD.ods file from the
ansible container to extract all the relevant information and
verifies the following

    1. IP addresses in DSD are reachable from each VM
    2. Ensures the disk partitions match the DSD on each VM
    3. Gathers CPU details from each VM
    4. Determines if hyperthreading is enabled on each VM
    5. Highlights what network ports are open on each VM
    6. Shows any network ports unopened based off cluster personality

NOTE:
If there are any failures during the test a report is generated
on the output of the python script
"""

from pyexcel_ods import get_data
import paramiko
import json
import pdb

data = get_data("/home/kudos/ansible/vars/DSD.ods")

cluster_personality = data.get("Other")[22][1]
banner = 60
VM_Disk = {}
DSD_Disk = {}

#######################################################
vm_ips = {}
ports = {}
interface_plus_ips = {}

########################################################
disk_report = {}
network_report = {}
CPU_Reports = {}
network_port_diff = {}

########################################################
TestDisk = {'/docker': '140 GB',
            '/var': '20 GB',
            '/tmp': '19.5 GB',
            '/home': '5 GB',
            '/var/cores': '20 GB',
            '/boot': '0.5 GB',
            '/commit': '10 GB',
            '/apps': '100 GB',
            '/': '5 GB',
            '/var/log': '10 GB',
            '/opt': '10 GB',
            '/logs': '20 GB',
            '/data': '10 GB',
            '/tc-image': '10 GB'}

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

cluster_types_and_ports = {
    "SMSC": ["2222", "8888", "2775", "29997", "50000", "25", "8090", "2525", "22", "111"],
    "MMSC": ["2222", "8888", "2775", "29997", "50000", "25", "8090", "2525", "22", "111", "8090"],
    "IMX": ["2222", "8888", "2775", "29997", "50000", "25", "8090", "2525", "22", "111", "8088", "8091", "443"],
    "INSIGHT": ["2222", "8888", "2775", "29997", "50000", "25", "8090", "2525", "22", "111", "8087"],
    "INSCARE": ["2222", "8888", "2775", "29997", "50000", "25", "8090", "2525", "22", "111", "8087"]
}


def read_IP_Addresses_from_DSD():
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
                if (data.get("Cluster")[interfaces+1] and data.get("Cluster")[interfaces+2]) and\
                        (data.get("Cluster")[interfaces+1][0] or data.get("Cluster")[interfaces+2][0]) is not '':
                    interface_plus_ips.update(
                        {
                            str(data.get("Cluster")[interfaces][0]):
                                [
                                    str(data.get("Cluster")[interfaces][1]),
                                    str(data.get("Cluster")[interfaces+1][0]),
                                    str(data.get("Cluster")[interfaces+2][0])
                                ]
                        }
                    )
    print interface_plus_ips


def read_disk_partitions_from_DSD():
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


def create_hostname_ip_matrix():
    """
    Method to create hostname vs IP address
    matrix that is more efficiently referenced
    rather than using interface_plus_ips
    :return: Populates vm_ips dictionary
    """
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    for host_ip in interface_plus_ips.get("OAM VLAN"):
        ssh.connect(host_ip, username='centos', password='centos', allow_agent=True)
        _, hostname, _ = ssh.exec_command('hostname')
        hostname = str(hostname.readlines()[0]).strip('\n')
        vm_ips[hostname] = host_ip
        ssh.close()


def ping_vm_ip_addresses():
    """
    This method is responsible for pinging the various
    IP address on different networks between nodes by
    SSH-ing into the different VMs in the cluster
    :return: N/A
    """
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    for host_ip, hostname in zip(vm_ips.itervalues(), vm_ips.keys()):
        print "-" * banner
        print "SSH-ing to VM " + hostname + "\n"
        print "-" * banner
        for network, ips in interface_plus_ips.iteritems():
            if "SIGTRAN VLAN " in network:
                continue
            else:
                print "Testing Network " + network + "\n"
                for ip in ips:
                    ssh.connect(host_ip, username='centos', password='centos', allow_agent=True)
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


def verify_disk_mount_sizes():
    """
    Method that compares the DSD Disk partitions
    with the VM disk partitions
    :return: Nothing
    """
    # VM_Disk = TestDisk
    for dsd_partition in DSD_Disk.keys():
        if dsd_partition in VM_Disk.keys():
            # Convert MB to GB for consistency
            if ("M" or "MB") in VM_Disk[dsd_partition]:
                VM_Disk[dsd_partition] = \
                    str(round
                        (float(
                            VM_Disk[dsd_partition].strip(' M'))*0.001, 1)) + " GB"
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


def get_disk_space_from_vm():
    """
    Method: get_disk_space_from_vm
    Purpose: To SSH into a VM and run df -h
    """
    for host_ip, hostname in zip(vm_ips.itervalues(), vm_ips.keys()):
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(host_ip, username='centos', password='centos')
        _, console_output, _ = ssh.exec_command('df -h')
        lines = console_output.readlines()
        print "-" * banner
        print "SSH-ing to VM " + hostname + "\n"
        print "-" * banner
        for i in range(1, len(lines)):
            VM_Disk.update({lines[i].split()[5]: lines[i].split()[1]})
        print "-" * banner
        print hostname + " Completed "
        print "-" * banner
        ssh.close()
        verify_disk_mount_sizes()


def get_CPU_and_Memory():
    """
    Method that gets CPU specs and determines if hyperthreading
    is enabled on nodes or not
    :return: Updates the CPU report at end of method
    """
    for host_ip, hostname in zip(vm_ips.itervalues(), vm_ips.keys()):
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(host_ip, username='centos', password='centos')
        _, console_output, _ = ssh.exec_command('lscpu')
        lines = console_output.readlines()
        ssh.close()
        CPU_Reports[hostname] = {}
        CPU_Reports[hostname][host_ip] = host_ip
        CPU_Reports[hostname]["CPUs"] = int(lines[3].split()[1])
        CPU_Reports[hostname]["CoreThreads"] = int(lines[5].split()[3])
        CPU_Reports[hostname]["Sockets"] = int(lines[7].split()[1])


def compare_network_ports():
    """
    Compare the network ports gotten from
    each VM and the clusters personality type
    and populate the port_discrepencies
    :return:
    """
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


def read_open_network_ports():
    """
    Method that returns a list of open TCP Network
    Ports on a given node in the cluster
    :return: List of given network ports
    """
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    port = []
    for hostname, host_ip in zip(vm_ips.keys(), vm_ips.values()):
        ssh.connect(host_ip, username='centos', password='centos')
        print "-" * banner
        print "Scanning open ports remote host", hostname
        print "-" * banner
        ###  List of open TCP ports
        ###  netstat -vatn | grep -i LISTEN
        _, open_ports, _ = ssh.exec_command('netstat -vatn | grep -i LISTEN')
        port_list = open_ports.readlines()
        ssh.close()

        for port_numbers in port_list:
            if port_numbers.split()[3].split(":")[1] == "":
                continue
            else:
                port.append(port_numbers.split()[3].split(":")[1])

        ports.update({hostname: port})
        port = []
    compare_network_ports()


def show_reports():
    """
    Collate any errors found into a report
    :return:
    """
    #### CPU Reporting ###
    if CPU_Reports:
        for hostnames in CPU_Reports.keys():
            print "-" * banner
            print hostnames
            if CPU_Reports[hostnames]["CoreThreads"] > 1:
                CPU_Reports[hostnames]["Threading "] = " Enabled"
            else:
                CPU_Reports[hostnames]["Threading "] = " Disabled"
            if CPU_Reports[hostnames]["CoreThreads"] * CPU_Reports[hostnames]["Sockets"] != \
                    CPU_Reports[hostnames]["CPUs"]:
                print "-" * banner
                print "WARNING: MISMATCHED (CORE THREADS * SOCKETS) Vs CPUs"
                print "-" * banner
            print "CPUs " + str(CPU_Reports[hostnames]["CPUs"])
            print "Hyper-Threading " + CPU_Reports[hostnames]["Threading "]
            print "Core Threads " + str(CPU_Reports[hostnames]["CoreThreads"])
            print "Sockets " + str(CPU_Reports[hostnames]["Sockets"])
            print "-" * banner
    ### Network Ports Vs Cluster Personality ###
    if network_port_diff:
        print "-" * banner
        print "Errors found with un-opened Network Ports "
        print "-" * banner
        print network_port_diff
    if ports:
        print "**" * banner
        print "Following Network Ports are open on each node respectively"
        print "**" * banner
        print json.dumps(ports, sort_keys=True, indent=4)
    ### Unreachable Network Addresses ###
    if network_report:
        print "-" * banner
        print "Errors found on the following Networks "
        print "-" * banner
        print json.dumps(network_report, sort_keys=True, indent=4)
    else:
        print "**" * banner
        print "PASS: No Network Issues found"
        print "**" * banner
    ### Disk Reporting ###
    if disk_report:
        print "-" * banner
        print "Errors found in the following Disk Partitions "
        print "-" * banner
        print json.dumps(disk_report, sort_keys=True, indent=4)
    else:
        print "**" * banner
        print "PASS: No Disk Issues found"
        print "**" * banner


if __name__ == '__main__':
    # Reading Information from DSD
    print "=" * banner
    print "READING INFORMATION FROM THE CUSTOMERS DSD"
    print "=" * banner
    read_IP_Addresses_from_DSD()
    read_disk_partitions_from_DSD()

    print "=" * banner
    print "CREATING HOSTNAME MATRIX"
    print "=" * banner
    create_hostname_ip_matrix()

    print "=" * banner
    print "Beginning Multi-Threading CPU Test"
    print "=" * banner
    get_CPU_and_Memory()

    print "=" * banner
    print "Beginning Network Test"
    print "=" * banner
    ping_vm_ip_addresses()

    print "=" * banner
    print "Beginning Network Port Test"
    print "=" * banner
    read_open_network_ports()

    print "=" * banner
    print "Beginning Disk Partition Test"
    print "=" * banner
    get_disk_space_from_vm()

    print "=" * banner
    print " Reports"
    print "=" * banner
    show_reports()
