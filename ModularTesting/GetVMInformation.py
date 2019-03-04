import paramiko

services = ["NetworkManager",
            "abrt-ccpp",
            "abrtd",
            "abrt-oops",
            "avahi-daemon",
            "avahi-dnsconfd" ,
            "chronyd",
            "dnsmasq" ,
            "firewalld",
            "ip6tables" ,
            "iptables",
            "kdump",
            "postfix",
            "rhnsd",
            "rpcgssd" 
            "rpcidmapd",
            "rpcsvcgssd",
            "sendmail",
            "wpa_supplicant"
            ]

banner = 60

#######################################################
ports = {}

########################################################

########################################################
# TestDisk = {'/docker': '140 GB',
#             '/var': '20 GB',
#             '/tmp': '19.5 GB',
#             '/home': '5 GB',
#             '/var/cores': '20 GB',
#             '/boot': '0.5 GB',
#             '/commit': '10 GB',
#             '/apps': '100 GB',
#             '/': '5 GB',
#             '/var/log': '10 GB',
#             '/opt': '10 GB',
#             '/logs': '20 GB',
#             '/data': '10 GB',
#             '/tc-image': '10 GB'}


class GetVMSpecs:
    """
    Class that obtains all the relevant information from the
    VMs within a given messaging cluster
    """
    def __init__(self):
        """
        init method
        """
        self.username = "centos"
        self.password = "centos"

    def create_hostname_ip_matrix(self, interface_plus_ips):
        """
        Method to create hostname vs IP address
        matrix that is more efficiently referenced
        rather than using interface_plus_ips
        :return: Populates vm_ips dictionary
        """
        vm_ips = {}
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        for host_ip in interface_plus_ips.get("OAM VLAN"):
            ssh.connect(host_ip, username=self.username, password=self.password, allow_agent=True)
            _, hostname, _ = ssh.exec_command('hostname')
            hostname = str(hostname.readlines()[0]).strip('\n')
            vm_ips[hostname] = host_ip
            ssh.close()
        return vm_ips

    def get_disk_space_from_vm(self, vm_ips):
        """
        Method: get_disk_space_from_vm
        Purpose: To SSH into a VM and run df -h
        return: VM_Disk dictionary
        """
        VM_Disk = {}

        for host_ip, hostname in zip(vm_ips.itervalues(), vm_ips.keys()):
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(host_ip, username=self.username, password=self.password)
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
        return VM_Disk

    def get_CPU_and_Memory(self, vm_ips):
        """
        Method that gets CPU specs and determines if hyperthreading
        is enabled on nodes or not
        :return: Updates the CPU report at end of method
        """
        CPU_Reports = {}
        VMFlag = False
        for host_ip, hostname in zip(vm_ips.itervalues(), vm_ips.keys()):
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(host_ip, username=self.username, password=self.password)
            _, console_output, _ = ssh.exec_command('lscpu')
            lines = console_output.readlines()
            ssh.close()
            for vmcheck in lines:
                if "VMware" in vmcheck:
                    VMFlag = True
            CPU_Reports[hostname] = {}
            CPU_Reports[hostname][host_ip] = host_ip
            CPU_Reports[hostname]["CPUs"] = int(lines[3].split()[1])
            CPU_Reports[hostname]["CoreThreads"] = int(lines[5].split()[3])
            CPU_Reports[hostname]["Sockets"] = int(lines[7].split()[1])
            CPU_Reports[hostname]["VMFlag"] = VMFlag
        return CPU_Reports

    def read_open_network_ports(self, vm_ips):
        """
        Method that returns a list of open TCP Network
        Ports on a given node in the cluster
        :return: List of given network ports
        """
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        port = []
        for hostname, host_ip in zip(vm_ips.keys(), vm_ips.values()):
            ssh.connect(host_ip, username=self.username,  password=self.password)
            print "-" * banner
            print "Scanning open ports remote host", hostname
            print "-" * banner
            ###  List of open TCP ports
            ###  netstat -vatn | grep -i LISTEN
            # netstat -an
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
        return ports

    def is_active(self, host_ip):
        """Return True if service is running"""
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        for service in services:
            cmd = '/bin/systemctl status %s.service' % service
            ssh.connect(host_ip, username=self.username, password=self.password)
            _, stdout_list, _ = ssh.exec_command(cmd)
            output = stdout_list.readlines()
            ssh.close()
            if "Active: active (running)" in output[2]:
                return True
            else:
                continue

    @staticmethod
    def stop(host_ip):
        """
        Method that will kill any unnecessary linux services running the background
        PROBLEM: Root password changes from env to env
        """
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(host_ip, username='root', password="")
        for service in services:
            cmd = '/bin/systemctl stop %s.service' % service
            _, stdout_list, _ = ssh.exec_command(cmd)
