from kube_plugin import get_docker
from cloudify import ctx
from fabric.api import run,sudo,put
import os.path
import subprocess
import time

def start_node():
  if(not ctx.node.properties['install']):
    return

  if(ctx.node.properties['install_docker']):
    get_docker()
  
  master_ip=ctx.instance.runtime_properties['master_ip']
  master_port=ctx.instance.runtime_properties['master_port']

  res=sudo("set -m;docker -d -H unix:///var/run/docker-bootstrap.sock -p /var/run/docker-bootstrap.pid --iptables=false --ip-masq=false --bridge=none --graph=/var/lib/docker-bootstrap 2> /var/log/docker-bootstrap.log 1> /dev/null </dev/null &",shell=True)
  if(res.return_code):
    return(res.return_code)

  time.sleep(2)
  
  sudo("service docker stop",shell=True)
  
  #run flannel
  
  output=sudo("docker -H unix:///var/run/docker-bootstrap.sock run -d --net=host --privileged -v /dev/net:/dev/net quay.io/coreos/flannel:0.5.0 /opt/bin/flanneld --etcd-endpoints=http://{}:4001".format(master_ip),shell=True)

  # get container id
  cid=output.strip()
  
  # get flannel subnet settings
  flannel=sudo("docker -H unix:///var/run/docker-bootstrap.sock exec {} cat /run/flannel/subnet.env".format(cid),shell=True)
  flannel=";".join(flannel.split())

  # edit docker config
  script=os.path.abspath("kube_plugin/edit_docker_config.py")
  put(script,"/tmp/edit_docker_config.py")
  sudo("python /tmp/edit_docker_config.py '{}'".format(flannel),shell=True)

  # remove existing docker bridge
  sudo("/sbin/ifconfig docker0 down",shell=True)
  sudo("apt-get install -y bridge-utils",shell=True)
  sudo("brctl delbr docker0",shell=True)

  # restart docker
  sudo("service docker start",shell=True)
  
  # run the kubelet
  sudo("docker run --net=host -d -v /var/run/docker.sock:/var/run/docker.sock  gcr.io/google_containers/hyperkube:v1.0.1 /hyperkube kubelet --api-servers=http://{}:{} --v=2 --address=0.0.0.0 --enable-server --hostname-override=$(hostname -i) --cluster-dns=10.0.0.10 --cluster-domain=cluster.local".format(master_ip,master_port),shell=True)
  
  # run the proxy
  sudo("docker run -d --net=host --privileged gcr.io/google_containers/hyperkube:v1.0.1 /hyperkube proxy --master=http://{}:{} --v=2".format(master_ip,master_port),shell=True)
