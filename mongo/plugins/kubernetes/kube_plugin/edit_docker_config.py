import sys
import subprocess

flannel=sys.argv[1]

# edit docker config
with open("/tmp/docker","w") as fd:
  with open("/etc/default/docker","r") as fdin:
    for line in fdin:
      fd.write(line)
with open("/tmp/docker","a") as fd:
  fd.write(flannel+"\n")
  fd.write('DOCKER_OPTS="--bip=${FLANNEL_SUBNET} --mtu=${FLANNEL_MTU}"\n')

subprocess.call("sudo mv /tmp/docker /etc/default/docker",shell=True)
