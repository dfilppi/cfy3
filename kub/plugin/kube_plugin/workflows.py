from cloudify.decorators import workflow
from cloudify.workflows import ctx
import re
import requests
from fabric.api import run,env


@workflow
def test(**kwargs):
  master=get_ip(kwargs['master'])
  masternode=ctx.get_node(kwargs['master'])
  url='http://'+master
  fabenv={}
  fabenv['user']=masternode.properties['ssh_username']
  fabenv['password']=masternode.properties['ssh_password']
  fabenv['key_filename']=masternode.properties['ssh_keyfilename']
  fabenv['host_string']=masternode.properties['ssh_username']+'@'+masternode.properties['ip']
  fabenv['port']=masternode.properties['ssh_port']
  kubeclient(url,fabenv).runapp()

class kubeclient(object):
  def __init__(self,url,fabric_env):
    self._url=url
    self._env=fabric_env
    env.update(fabric_env)

  # simple run app.  runs replication controller too
  # uses default namespace
  def runapp(self):
    run("./kubectl -s http://localhost:8080 run nginx --image=nginx --port=80")
    run("./kubectl expose rc nginx --port=80")   
    

def get_ip(master):
  if(ctx.local):
    return ctx.get_node(master).properties['ip']
  else:
    raise('not implemented')  # need to get default instance in cloud case
