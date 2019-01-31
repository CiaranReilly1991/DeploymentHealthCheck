"""
This python script allows us to test the IP addresses are
reachable from within the cluster and compare the DSD disk partitions
to what's seen on the VM

Currently the script requires the DSD.ods file from the
ansible container to extract all the relevant IP networks info and
disk partitions and should verify the addresses respond successfully
and the mount sizes are correct.

NOTE:
Further validation tightening needs to be put in place when a ping
fails to reach the IP in question. Currently if a ping fails it
will proceed to the following IP from the DSD as so forth
"""

from pyexcel_ods import get_data
import paramiko
import pdb

VM_Disk = {}
DSD_Disk = {}
disk_report = {}
network_report ={}

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

interface_plus_ips ={}

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

data = get_data("/home/kudos/ansible/vars/DSD.ods")


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


def ping_vm_ip_addresses():
    """
    This method is responsible for pinging the various
    IP address on different networks between nodes by
    SSH-ing into the different VMs in the cluster
    :return: N/A
    """

    ssh = paramiko.SSHClient()

    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    for host_ip in interface_plus_ips.get("OAM VLAN"):
        print "------------------------------------"
        print "SSH-ing to VM " + host_ip + "\n"
        print "------------------------------------"
        for network, ips in interface_plus_ips.iteritems():
            if "SIGTRAN VLAN " in network:
                continue
            else:
                print "Testing Network " + network + "\n"
                for ip in ips:
                    print "Pinging IP " + ip + " from network " + network + " on node " + host_ip + "\n"
                    ssh.connect(host_ip, username='centos', password='centos', allow_agent=True)
                    _, resp, _ = ssh.exec_command('/usr/bin/ping -c 3 ' + ip)
                    print resp.readlines() # This line prints all the ping responses
                    try:
                        assert (len(resp.readlines()) < 4)
                    except AssertionError as e:
                        print e
                        #print host_ip + " ERROR found " + ip
                        network_report[network] = [ip + " IP Not Ping-able from " + host_ip]
                        continue
        print "------------------------------------"
        print host_ip + " Completed " + "\n"
        print "------------------------------------"
        ssh.close()


def verify_disk_mount_sizes():
    """
    Compare the disk sizes between VM and DSD and
    store the result in an ERROR report dictionary
    """
    #VM_Disk = TestDisk
    for dsd_partition in DSD_Disk.keys():
        if dsd_partition in VM_Disk.keys():
            if DSD_Disk[dsd_partition].strip('GB')[0] == VM_Disk[dsd_partition].strip('GB')[0]:
                print dsd_partition + " Partition size is correct"
            else:
                disk_report[dsd_partition] = [DSD_Disk[dsd_partition],
                                              VM_Disk[dsd_partition]]
                continue


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
                {str(data.get("OS")[line][0]):
                     str(data.get("OS")[line][4]) + " GB"})
        else:
            break


def get_disk_space_from_vm():
    """
    Method: get_disk_space_from_vm
    Purpose: To SSH into a VM and run df -h
    """
    for host_ip in interface_plus_ips.get("OAM VLAN"):
        print "------------------------------------"
        print "SSH-ing to VM " + host_ip + "\n"
        print "------------------------------------"
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(host_ip, username='centos', password='centos')
        _, console_output, _ = ssh.exec_command('df -h')
        lines = console_output.readlines()
        for i in range(0, len(lines)):
            if i is 0:
                continue
            else:
                VM_Disk.update({lines[i].split()[5]: lines[i].split()[1]})
        print "------------------------------------"
        print host_ip + " Completed " + "\n"
        print "------------------------------------"
    ssh.close()

    verify_disk_mount_sizes()


def show_error_report():
    """
    Collate the errors found into a report
    :return:
    """
    if network_report:
        print "---------------------------------------------------"
        print "Errors found on the following Networks "
        print "---------------------------------------------------"
        print network_report
    if disk_report:
        print "---------------------------------------------------"
        print "Errors found in the following Disk Partitions "
        print "---------------------------------------------------"
        print disk_report


if __name__ == '__main__':
    # Reading Information from DSD
    print "======================================================="
    print "READING INFORMATION FROM THE CUSTOMERS DSD"
    print "======================================================="
    read_IP_Addresses_from_DSD()
    read_disk_partitions_from_DSD()

    print "======================================================="
    print "Beginning Network Test"
    print "======================================================="
    ping_vm_ip_addresses()

    print "======================================================="
    print "Beginning Disk Partition Test"
    print "======================================================="
    get_disk_space_from_vm()

    print "======================================================="
    print "ERROR Reports"
    print "======================================================="
    show_error_report()
