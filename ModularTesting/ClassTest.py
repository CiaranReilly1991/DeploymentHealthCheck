import GetDSDInformation
import CompareDSDVM
import GetVMInformation
import json

if __name__ == '__main__':

    banner = 60
    ReadDSD = GetDSDInformation.ReadDSDSpec()
    GetVMInfo = GetVMInformation.GetVMSpecs()
    TestReport = CompareDSDVM.Test_DSDVsVM()

    print "=" * banner
    print "READING INFORMATION FROM THE CUSTOMERS DSD"
    print "=" * banner
    cluster_personality = GetDSDInformation.cluster_personality
    cluster_ports = GetDSDInformation.cluster_types_and_ports
    DSD_Disk = ReadDSD.read_disk_partitions_from_DSD()
    interface_and_ips = ReadDSD.read_IP_Addresses_from_DSD()

    if (cluster_ports or DSD_Disk or interface_and_ips) == {}:
        print "* * *" * banner
        print "ERROR: READING DSD INFORMATION"
        print "* * *" * banner
    else:
        print "=" * banner
        print "READING INFORMATION FROM THE VMs"
        print "=" * banner
        GetVMInfo = GetVMInformation.GetVMSpecs()

        print "=" * banner
        print "CREATING HOSTNAME MATRIX"
        print "=" * banner
        vm_ips = GetVMInfo.create_hostname_ip_matrix(interface_and_ips)

        print "=" * banner
        print "GETTING DISK PARTITION SIZES"
        print "=" * banner
        VM_Disk = GetVMInfo.get_disk_space_from_vm(vm_ips)

        print "=" * banner
        print "READING OPEN NETWORK PORTS PER NODE"
        print "=" * banner
        ports = GetVMInfo.read_open_network_ports(vm_ips)

        print "=" * banner
        print "READING CPU Hyper-Threading"
        print "=" * banner
        cpu_reports = GetVMInfo.get_CPU_and_Memory(vm_ips)

        print "=" * banner
        print "Beginning Network Test"
        print "=" * banner
        ntwk_reach_report = \
            TestReport.ping_vm_ip_addresses(vm_ips, interface_and_ips)

        print "=" * banner
        print "Beginning Network Port Test"
        print "=" * banner
        port_diff = TestReport.compare_network_ports(ports, cluster_personality)

        print "=" * banner
        print "Beginning Disk Partition Test"
        print "=" * banner
        disk_report = TestReport.verify_disk_mount_sizes(DSD_Disk, VM_Disk)

        print "=" * banner
        print " Reports"
        print "=" * banner

        #### CPU Reporting ###
        if cpu_reports:
            for hostnames in cpu_reports.keys():
                print "-" * banner
                print hostnames
                if cpu_reports[hostnames]["CoreThreads"] > 1:
                    cpu_reports[hostnames]["Threading "] = " Enabled"
                else:
                    cpu_reports[hostnames]["Threading "] = " Disabled"
                if cpu_reports[hostnames]["CoreThreads"] * cpu_reports[hostnames]["Sockets"] != \
                        cpu_reports[hostnames]["CPUs"]:
                    print "-" * banner
                    print "WARNING: MISMATCHED (CORE THREADS * SOCKETS) Vs CPUs"
                    print "-" * banner
                print "CPUs " + str(cpu_reports[hostnames]["CPUs"])
                print "Hyper-Threading " + cpu_reports[hostnames]["Threading "]
                print "Core Threads " + str(cpu_reports[hostnames]["CoreThreads"])
                print "Sockets " + str(cpu_reports[hostnames]["Sockets"])
                print "-" * banner

        ### Network Ports Vs Cluster Personality ###
        if port_diff:
            print "-" * banner
            print "Errors found with un-opened Network Ports "
            print "-" * banner
            print port_diff
        if ports:
            print "**" * banner
            print "Following Network Ports are open on each node respectively"
            print "**" * banner
            print json.dumps(ports, sort_keys=True, indent=4)
        ### Unreachable Network Addresses ###
        if ntwk_reach_report:
            print "-" * banner
            print "Errors found on the following Networks "
            print "-" * banner
            print json.dumps(ntwk_reach_report, sort_keys=True, indent=4)
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