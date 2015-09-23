from kube_plugin import get_docker
from cloudify import ctx
from fabric.api import run,sudo,put,env
import os.path
import subprocess
import time

def start_master():
  ctx.logger.info("!!Node properties:{}".format(str(ctx.node.properties)))
  ctx.logger.info("!!env:{}".format(str(env)))

  if(not ctx.node.properties['install']):
    return

  if(ctx.node.properties['install_docker']):
    get_docker()
  
  master_ip=ctx.node.properties['ip']
  master_port=ctx.node.properties['master_port']

  res=sudo('set -m; nohup docker -d -H unix:///var/run/docker-bootstrap.sock -p /var/run/docker-bootstrap.pid --iptables=false --ip-masq=false --bridge=none --graph=/var/lib/docker-bootstrap 2> /var/log/docker-bootstrap.log 1> /dev/null </dev/null &',shell=True)
  if(res.return_code):
    return(res.return_code)

  time.sleep(2)
  
  # start etcd
  res=sudo("docker -H unix:///var/run/docker-bootstrap.sock run --net=host -d gcr.io/google_containers/etcd:2.0.12 /usr/local/bin/etcd --addr=127.0.0.1:4001 --bind-addr=0.0.0.0:4001 --data-dir=/var/etcd/data",shell=True)
  
  if(res.return_code):
    return(res.return_code)
  
  time.sleep(2)

  # set cidr range for flannel
  sudo('docker -H unix:///var/run/docker-bootstrap.sock run --net=host gcr.io/google_containers/etcd:2.0.12 etcdctl set /coreos.com/network/config \'{ "Network": "10.1.0.0/16" }\'',shell=True)
  
  # stop docker
  
  sudo("service docker stop",shell=True)
  
  #run flannel
  
  output=sudo("docker -H unix:///var/run/docker-bootstrap.sock run -d --net=host --privileged -v /dev/net:/dev/net quay.io/coreos/flannel:0.5.0",shell=True)
  
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
  
  # start the master
  sudo("docker run --net=host -d -v /var/run/docker.sock:/var/run/docker.sock  gcr.io/google_containers/hyperkube:v1.0.1 /hyperkube kubelet --api-servers=http://localhost:{} --v=2 --address=0.0.0.0 --enable-server --hostname-override=127.0.0.1 --config=/etc/kubernetes/manifests-multi --cluster-dns=10.0.0.10 --cluster-domain=cluster.local".format(master_port),shell=True)
  
  # run the proxy
  sudo("docker run -d --net=host --privileged gcr.io/google_containers/hyperkube:v1.0.1 /hyperkube proxy --master=http://127.0.0.1:{} --v=2".format(master_port),shell=True)

  # get kubectl
  run("wget http://storage.googleapis.com/kubernetes-release/release/v1.0.1/bin/linux/amd64/kubectl -O kubectl")
  run("chmod +x kubectl")
