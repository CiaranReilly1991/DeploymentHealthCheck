# DeploymentHealthCheck.py
Runs from deployment container for various sites, to run ensure the following is in place

1. All the python files are placed in the omn.deploy docker container, specifically under the 'ansible/var' directory, where the DSD.ods resides
2. Run the health check before/after deployment is complete (It shouldnt matter)
3. Command to run the health check on a given deployment it "python DeploymentHealthCheck.py"
4. The size of the cluster does not matter, if its a big cluster you maybe waiting a while. 

Any questions contact me.
