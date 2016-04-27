from cloudify.decorators import operation
from kube_plugin import get_docker,edit_docker_config
from cloudify import ctx
import os
import subprocess
import time

@operation
def start_master(**kwargs):
  if(not ctx.node.properties['install']):
    return

  os.chdir(os.path.expanduser("~"))

  subprocess.call("sudo apt-get update",shell=True)

  if(ctx.node.properties['install_docker']):
    ctx.logger.info("getting docker")
    get_docker(ctx)

  master_port=ctx.node.properties['master_port']

  ctx.logger.info("in start_master")

  subprocess.Popen(['sudo','nohup','docker','daemon','-H','unix:///var/run/docker-bootstrap.sock','-p','/var/run/docker-bootstrap.pid','--iptables=false','--ip-masq=false','--bridge=none','--graph=/var/lib/docker-bootstrap'],stdout=open('/dev/null'),stderr=open('/tmp/docker-bootstrap.log','w'),stdin=open('/dev/null'))
  time.sleep(2)

  # start etcd
  res=os.system("sudo docker -H unix:///var/run/docker-bootstrap.sock run --net=host -d gcr.io/google_containers/etcd:2.0.12 /usr/local/bin/etcd --addr=127.0.0.1:4001 --bind-addr=0.0.0.0:4001 --data-dir=/var/etcd/data")

  ctx.logger.info("start etcd:"+str(res))

  if(res):
    return(res)

  time.sleep(2)

  # set cidr range for flannel
  os.system('sudo docker -H unix:///var/run/docker-bootstrap.sock run --net=host gcr.io/google_containers/etcd:2.0.12 etcdctl set /coreos.com/network/config \'{ "Network": "10.1.0.0/16" }\'')

  ctx.logger.info("set flannel cidr")

  # stop docker

  os.system("sudo service docker stop")

  #run flannel

  pipe=subprocess.Popen(['sudo','docker','-H','unix:///var/run/docker-bootstrap.sock','run','-d','--net=host','--privileged','-v','/dev/net:/dev/net','quay.io/coreos/flannel:0.5.3'],stderr=open('/dev/null'),stdout=subprocess.PIPE)

  # get container id
  cid=pipe.stdout.read().strip()
  pipe.wait()

  # get flannel subnet settings
  output=os.popen("sudo docker -H unix:///var/run/docker-bootstrap.sock exec {} cat /run/flannel/subnet.env".format(cid))
  flannel=";".join(output.read().split())

  # edit docker config
  edit_docker_config(flannel)

  # remove existing docker bridge
  os.system("sudo /sbin/ifconfig docker0 down")
  os.system("sudo apt-get install -y bridge-utils")
  os.system("sudo brctl delbr docker0")

  # restart docker
  os.system("sudo service docker start")

  # start the master
  subprocess.call("sudo docker run --net=host -d -v /var/run/docker.sock:/var/run/docker.sock  gcr.io/google_containers/hyperkube:v1.0.1 /hyperkube kubelet --api-servers=http://localhost:{} --v=2 --address=0.0.0.0 --enable-server --hostname-override=127.0.0.1 --config=/etc/kubernetes/manifests-multi --cluster-dns=10.0.0.10 --cluster-domain=cluster.local".format(master_port),shell=True)

  # run the proxy
  subprocess.call("sudo docker run -d --net=host --privileged gcr.io/google_containers/hyperkube:v1.0.1 /hyperkube proxy --master=http://127.0.0.1:{} --v=2".format(master_port),shell=True)

  # get kubectl
  subprocess.call("wget http://storage.googleapis.com/kubernetes-release/release/v1.0.1/bin/linux/amd64/kubectl -O kubectl",shell=True)
  subprocess.call("chmod +x kubectl",shell=True)

