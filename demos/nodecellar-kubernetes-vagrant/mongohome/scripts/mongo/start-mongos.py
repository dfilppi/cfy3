import sys
import socket
import time
import subprocess

from cloudify import ctx
from cloudify import utils
from cloudify_rest_client import CloudifyClient

def port_avail(port):
  s=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
  try:
    s.bind((socket.gethostname(),port))
    s.close()
    return True
  except:
    return False

#
#  find an open socket starting at start point
#
def next_port(start):
  s=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
  for p in range(start,65535):
    try:
      s.bind((socket.gethostname(),p))
      s.close()
      return p
    except:
      if (p==65535):
        return -1

def wait_for_server(port,server_name):
  started=False

  ctx.logger.info("Running {} liveness detector on port {}".format(server_name,port))

  for i in range(1,120):
    if port_avail(port):
      ctx.logger.info("{} has not started. waiting...".format(server_name))
      time.sleep(1)
    else:
      started=True
      break

  if not started: 
    ctx.logger.error("{} failed to start. waiting for 120 seconds".format(server_name))
    sys.exit(1)


port=ctx.node.properties['port']
##get available port
port=next_port(port)
ctx.instance.runtime_properties['mongo_port']=port
ctx.logger.info("cfg instance port: {}".format(port))
mongo_binaries_path=ctx.instance.runtime_properties['mongo_binaries_path']

command="{}/bin/mongos --port {} --configdb {}".format(mongo_binaries_path,port,ctx.instance.runtime_properties['cfghosts'])
ctx.logger.info(command)
#sub=subprocess.Popen("nohup {} > /dev/null 2>&1".format(command),shell=True)
sub=subprocess.Popen(['nohup',
                     "{}/bin/mongos".format(mongo_binaries_path),
                     "--bind_ip","192.168.33.11",
                     "--port","{}".format(port),
                     "--configdb","{}".format(ctx.instance.runtime_properties['cfghosts'])])
#p=subprocess.Popen(['nohup','bash','-c','sleep 40'])
pid=sub.pid

wait_for_server(port,'Mongos')

# this runtime porperty is used by the stop-mongo script.
ctx.instance.runtime_properties['pid']=pid

ctx.logger.info( "Successfully started Mongos ({})".format(pid))
