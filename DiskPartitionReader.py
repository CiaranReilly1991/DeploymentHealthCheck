import paramiko
from pyexcel_ods import get_data
import pdb

VM_Disk = {}
DSD_Disk = {}
Report = {}

TestDisk = {'/docker': '140 G',
            '/var': '20 G',
            '/tmp': '19.5 G',
            '/home': '5 G',
            '/var/cores': '20 G',
            '/boot': '0.5 G',
            '/commit': '10 G',
            '/apps': '100 G',
            '/': '5 G',
            '/var/log': '10 G',
            '/opt': '10 G',
            '/logs': '20 G',
            '/data': '10 G',
            '/tc-image': '10 G'}

"""
Python script that will compare the DSD disk partitions 
to what's seen on the VM
"""

data = get_data("DSD_Du_MMSC_S2.ods")


"""
Compare the disk sizes between VM and DSD and
store the result in an ERROR report dictionary
"""


def verify_disk_mount_sizes():

    VM_Disk = TestDisk
    for dsd_partition in DSD_Disk.keys():
        if dsd_partition in VM_Disk.keys():
            if DSD_Disk[dsd_partition].strip('GB')[0] == VM_Disk[dsd_partition].strip('GB')[0]:
                print dsd_partition + " Partition size is correct"
            else:
                Report[dsd_partition] = [DSD_Disk[dsd_partition],
                                         VM_Disk[dsd_partition]]
                continue


"""
Method: read_disk_partitions_from_DSD
Purpose: To read disk partitions from DSD
Comments: 

DSD is currently set above, but we will 
eventually pass the DSD as an arguement 
when running the scripts. I've tested 
with a few DSD's and seems to work fine.

"""


def read_disk_partitions_from_DSD():
    disk_lines = range(15, len(data.get("OS")))
    for line in disk_lines:
        if "/" in (data.get("OS")[line][0]):
            # This line extracts the Partition and the Size in GB from the OS tab in the DSD
            DSD_Disk.update({str(data.get("OS")[line][0]): str(data.get("OS")[line][4]) + " GB"})
        else:
            break


"""
Method: get_disk_space_from_vm
Purpose: To SSH into a VM and run df -h
Comments:

Currently using my S2P MMSC @ 192.168.123.249, 
so validation still needs to be made once we
get the two dictionaries of data to compare

"""


def get_disk_space_from_vm():
    ssh = paramiko.SSHClient()

    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    ssh.connect('192.168.123.249', username='omndocker', password='omndocker')

    _, console_output, _ = ssh.exec_command('df -h')

    lines = console_output.readlines()

    for i in range(0, len(lines)):
        if i is 0:
            continue
        else:
            VM_Disk.update({lines[i].split()[5]: lines[i].split()[1]})

    ssh.close()

    verify_disk_mount_sizes()


def show_error_report():
    if Report:
        print "==================================================="
        print "Errors found in the following Disk Partitions "
        print "==================================================="
        print Report


if __name__ == '__main__':
    print "==================================================="
    print "Verifying Disk Space on Node 1 of Cluster"
    print "==================================================="
    read_disk_partitions_from_DSD()
    get_disk_space_from_vm()
    show_error_report()
    # print VM_Disk.keys()
    # print VM_Disk.values()

