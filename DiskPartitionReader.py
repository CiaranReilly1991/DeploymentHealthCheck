import paramiko
from pyexcel_ods import get_data

import pdb

VM_Disk = {}
DSD_Disk = {}

"""
Python script that will compare the DSD disk partitions 
to what's seen on the VM
"""

data = get_data("DSD_Du_MMSC_S2.ods")

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

    _, stdout, _ = ssh.exec_command('df -h')

    for line in stdout.readlines():
        #print line
        if "Filesystem" in line:
            print "Filtering First line"
        else:
            VM_Disk.update({line[0:12]: line[12:]})
            #print VM_Disk


if __name__ == '__main__':
    read_disk_partitions_from_DSD()
    print DSD_Disk
    get_disk_space_from_vm()
    print VM_Disk

######### Ignore this ##########################################
# disk = os.statvfs("/")
    # systems = psutil.disk_partitions(all=False)
    #
    # GB = 1.073741824e9
    #
    # capacity = disk.f_bsize * disk.f_blocks
    # available = disk.f_bsize * disk.f_bavail
    # used = disk.f_bsize * (disk.f_blocks - disk.f_bavail)
