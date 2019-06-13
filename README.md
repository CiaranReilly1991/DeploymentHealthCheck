# DeploymentHealthCheck.py
Runs from deployment container for various sites, to run ensure the following is in place

1. All the python files are placed in the omn.deploy docker container, specifically under the 'ansible/var' directory, where the DSD.ods resides
2. Run the health check before/after deployment is complete (It shouldnt matter)
3. Command to run the health check on a given deployment it "python DeploymentHealthCheck.py"
4. The size of the cluster does not matter, if its a big cluster you maybe waiting a while, so go make a coffee :-) 

# GetVMInformation.py
Gathers any details from the cluster VMs on site via SSH connectivity, and stores the information in a dictionary for later comparison

# GetDSDInformation.py
Parses DSD.ods files found on the deployment container for later testing and comparing

# CompareDSDVM.py
Test script where the extracted DSD information is compared with teh physical config found on a customer site

Any questions contact me.
