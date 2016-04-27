from cloudify.decorators import operation
from kube_plugin import get_docker, edit_docker_config
from cloudify import ctx
import os
import subprocess
import time
import socket
import fcntl
import struct


def get_ip_address(ifname):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    return socket.inet_ntoa(fcntl.ioctl(
        s.fileno(),
        0x8915,  # SIOCGIFADDR
        struct.pack('256s', ifname[:15])
    )[20:24])

@operation
def start_node(**kwargs):
  if(not ctx.node.properties['install']):
    return

  os.chdir(os.path.expanduser("~"))

  subprocess.call("sudo apt-get update",shell=True)

  if(ctx.node.properties['install_docker']):
    get_docker(ctx)
  
  master_ip=ctx.instance.runtime_properties['master_ip']
  master_port=ctx.instance.runtime_properties['master_port']


  ctx.logger.info("got inputs master_ip={} master_port={}".format(master_ip,master_port))

  subprocess.Popen(['sudo','nohup','docker','daemon','-H','unix:///var/run/docker-bootstrap.sock','-p','/var/run/docker-bootstrap.pid','--iptables=false','--ip-masq=false','--bridge=none','--graph=/var/lib/docker-bootstrap'],stdout=open('/dev/null'),stderr=open('/tmp/docker-bootstrap.log','w'),stdin=open('/dev/null'))

  time.sleep(2)
  
  os.system("sudo service docker stop")
  
  #run flannel
  
  pipe=subprocess.Popen(['sudo','docker','-H','unix:///var/run/docker-bootstrap.sock','run','-d','--net=host','--privileged','-v','/dev/net:/dev/net','quay.io/coreos/flannel:0.5.3','/opt/bin/flanneld','--etcd-endpoints=http://{}:4001'.format(master_ip)],stderr=open('/dev/null'),stdout=subprocess.PIPE)

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
  
  # run the kubelet
  subprocess.call("sudo docker run --net=host -d -v /var/run/docker.sock:/var/run/docker.sock  gcr.io/google_containers/hyperkube:v1.0.1 /hyperkube kubelet --api-servers=http://{}:{} --v=2 --address=0.0.0.0 --enable-server --hostname-override={} --cluster-dns=10.0.0.10 --cluster-domain=cluster.local".format(master_ip,master_port,get_ip_address('eth0')),shell=True)
  
  # run the proxy
  subprocess.call("sudo docker run -d --net=host --privileged gcr.io/google_containers/hyperkube:v1.0.1 /hyperkube proxy --master=http://{}:{} --v=2".format(master_ip,master_port),shell=True)
