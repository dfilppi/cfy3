Description:

Demonstrates a hybrid deployment on Vagrant using the simple manager and Kubernetes.  Result is the usual nodecellar demo.

Requirements:

* Vagrant: two VM config, one to host Kubernetes and nodejs, the other the Cloudify CLI and Mongodb
* Access to docker image on DockerHub for nodejs.  __DEMO REQUIRES INTERNET ACCESS__ (at least on the first run)
* A machine with at least 5GB free to launch the machines
* A machine with Virtualbox >= 4.3
* A machine with Vagrant >= 1.6.3

Instructions:

* Using the Vagrantfile in scripts/, bootstrap the environment
-- copy Vagrant file to an empty directory
-- from the directory execute: "vagrant up"
-- result:  two VMs, one named 'kub' and one named 'mongo'

* Start kubernetes on kub
-- ssh in: 'vagrant ssh kub'
-- copy scripts/startkub.sh to the home directory on 'kub'
-- install docker
---- sudo apt-get update
---- sudo apt-get wget
---- wget -O getdocker.sh get.docker.com
---- run getdocker.sh: 'sudo ./getdocker.sh'
---- test success: 'sudo docker ps'
-- start kubernetes: 'sudo ./startkub.sh'
-- get kubectl
---- 'wget https://storage.googleapis.com/kubernetes-release/release/v1.0.1/bin/linux/amd64/kubectl'
---- 'chmod +x kubectl'
-- test kubernetes: './kubectl get pods'  (should get just kubernetes itself)
-- get image: sudo docker pull dfilppi/nodecellar:v1

* Install cfy on mongo
-- ssh in: 'vagrant ssh mongo'
-- install cfy cli
---- sudo apt-get update
---- sudo apt-get install -y python-dev
---- sudo apt-get install -y python-virtualenv
---- virtualenv .
---- . bin/activate
---- pip install cloudify
---- test success: 'cfy --version'

* Run the blueprint
-- copy the contents of mongohome/ to the /home/vagrant dir on mongo
-- cd to cfy3/mongo
-- run 'cfy local install-plugins -p local-blueprint.yaml'
-- run 'cfy local init -p local-blueprint.yaml'
-- run 'cfy local execute -w install'
