from pyexcel_ods import get_data
import socket
import os
import paramiko
import pdb

"""
This python script allows us to test the IP addresses are 
reachable from within the cluster. 

Currently the script requires the DSD.ods file from the
ansible container to extract all the relevant IP and networks
and should verify the addresses respond successfully. 

NOTE: 
Further validation tightening needs to be put in place when a ping 
fails to reach the IP in question. Currently if a ping fails it 
will proceed to the following IP from the DSD as so forth
"""

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

#data = get_data("/home/kudos/ansible/vars/DSD.ods")
data = get_data("DSD_Du_MMSC_S2.ods")


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
        print "SSH-ing to VM " + host_ip
        for network, ips in interface_plus_ips.iteritems():
            if "SIGTRAN VLAN " in network:
                continue
            else:
                print "Testing Network " + network
                for ip in ips:
                    print "Pinging IP " + ip + " from network " + network
                    # pdb.set_trace()
                    ssh.connect(host_ip, username='centos', password='centos', allow_agent=True)
                    _, resp, _ = ssh.exec_command('/usr/bin/ping -c 3 ' + ip)
                    print resp.readlines()
                    if len(resp.readlines) < 4:
                        print "IP " + ip + " on " + network + " is dead"
                    else:
                        continue

        ssh.close()

if __name__ == '__main__':
    read_IP_Addresses_from_DSD()
    ping_vm_ip_addresses()

