## Description:

Demonstrates a hybrid local mode deployment on Vagrant using the simple manager and Kubernetes.  Result is the usual nodecellar demo.

## Requirements:

- Vagrant: two VM config, one to host Kubernetes and nodejs, the other the Cloudify CLI and Mongodb
- Access to docker image on DockerHub for nodejs.  __DEMO REQUIRES INTERNET ACCESS__ (at least on the first run)
- A machine with at least 5GB free to launch the machines
- A machine with Virtualbox >= 4.3
- A machine with Vagrant >= 1.6.3

## Instructions:
<ul>
 <li>Using the Vagrantfile in scripts/, bootstrap the environment
 <ul>
  <li> copy Vagrant file to an empty directory
  <li> from the directory execute: "vagrant up"
  <li> result:  two VMs, one named 'kub' and one named 'mongo'
  <ul>
   <li> use `vagrant status` to see what is running
   <li> sometimes one doesn't start and has to be started manually.  Use either `vagrant up kub` or `vagrant up mongo`.
 </ul>
</ul>

<ul>
<li> Start kubernetes on kub
 <ul>
  <li> ssh in: `vagrant ssh kub`
  <li> copy scripts/startkub.sh to the home directory on 'kub'
  <li> install docker
  <ul>
   <li>`sudo apt-get update`
   <li>`sudo apt-get wget`
   <li>`wget -O getdocker.sh get.docker.com`
   <li>run getdocker.sh: `sudo ./getdocker.sh`
   <li>test success: `sudo docker ps`
  </ul>
  <li>start kubernetes: `sudo ./startkub.sh`
   <li> get kubectl
   <ul>
    <li>`wget https://storage.googleapis.com/kubernetes-release/release/v1.0.1/bin/linux/amd64/kubectl`
    <li>`chmod +x kubectl`
   </ul>
   <li>test kubernetes: `./kubectl get pods`  (should get just kubernetes itself)
   <li>get image: `sudo docker pull dfilppi/nodecellar:v1`
 </ul>
</ul>

<ul>
<li>Install cfy on mongo
 <ul>
  <li>ssh in: `vagrant ssh mongo`
  <li>install cfy cli
  <ul>
   <li>`sudo apt-get update`
   <li>`sudo apt-get install -y python-dev`
   <li>`sudo apt-get install -y python-virtualenv`
   <li>`virtualenv .`
   <li>`. bin/activate`
   <li>`pip install cloudify`
   <li>test success: `cfy --version`
  </ul>
 </ul>
</ul>

<br>
There are two ways to run the demo: with the Kuberenetes nodes defined in the same blueprint as MongoDb, and with the Kuberenetes nodes defined in a separate blueprint from the mongo node.  The first has a more 'hybrid cloud' flavor, where the second is probably more useful in a 'microservices' context.

<b>Kubernetes and Mongo in the same blueprint</b>
<ul>
<li>Run the blueprint
 <ul>
  <li>copy the contents of mongohome/ to the /home/vagrant dir on mongo
  <li>cd to cfy3/mongo
  <li>run `cfy local install-plugins -p local-with-kub.yaml`
  <li>run `cfy local init -p local-with-kub.yaml`
  <li>run `cfy local execute -w install`
 </ul>
</ul>

<b>Kubernetes and Mongo in the separate blueprints</b>
<ul>
<li>Run the blueprints
 <ul>
  <li>copy the contents of mongohome/ to the /home/vagrant dir on mongo
  <li>cd to cfy3/mongo
  <li>run `cfy local install-plugins -p local-with-kub.yaml`
  <li>run `cfy local init -p local-simple.yaml`
  <li>run `cfy local execute -w install`.  This will start mongodb
  <li>create a subdir (tmp for example).  cd to tmp.
  <li>run `cp ../local-kub-node.yaml .`
  <li>run `cfy local init -p local-kub-node.yaml`
  <li>run `cfy local execute -w install`.  This will start the microservice on Kuberenetes.
 </ul>
</ul>

## Finish line
The demo is be available on http://192.168.33.10:3000
