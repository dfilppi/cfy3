from cloudify.decorators import workflow
from cloudify.workflows import ctx
import re
from fabric.api import run,env


#
# Run an image on the cluster pointed to by the master arg
#
@workflow
def kube_run(**kwargs):
  setfabenv(kwargs)
  optstr=buildopts(kwargs,{"dry_run":"dry-run"},{"port":"not _val_ == -1"},["dry_run"],['name','master'])
  ctx.logger.info("Running: {}".format(optstr))
  run("./kubectl -s http://localhost:8080 run "+" "+kwargs['name']+optstr)

#
# Expose an app
#
@workflow
def kube_expose(**kwargs):
  setfabenv(kwargs)
  optstr=buildopts(kwargs,{"target_port":"target-port","service_name":"service-name"},{"target_port":"not _val_ == -1"},[],['name','master','resource'])
  runstr="./kubectl -s http://localhost:8080 expose {} {} {}".format(kwargs['resource'],kwargs['name'],optstr)
  ctx.logger.info("Running: {}".format(runstr))
  run(runstr)
  
#
# Stop a resource (by name)
#
@workflow
def kube_stop(**kwargs):
  setfabenv(kwargs)
  optstr=buildopts(kwargs,{},{},["all"],['name','master','resource'])
  runstr="./kubectl -s http://localhost:8080 stop {} {} {}".format(kwargs['resource'],kwargs['name'],optstr)
  ctx.logger.info("Running: {}".format(runstr))
  run(runstr)
  
#
# Delete a resource (by name)
#
@workflow
def kube_delete(**kwargs):
  setfabenv(kwargs)
  optstr=buildopts(kwargs,{},{},["all"],['name','master','resource'])
  runstr="./kubectl -s http://localhost:8080 delete {} {} {}".format(kwargs['resource'],kwargs['name'],optstr)
  ctx.logger.info("Running: {}".format(runstr))
  run(runstr)

##################################################
#
# UTILITY
#
##################################################

# Construct the fabric environment from the supplied master
# node in kwargs
def setfabenv(kwargs):
  master=get_ip(kwargs['master'])
  masternode=ctx.get_node(kwargs['master'])
  url='http://'+master
  fabenv={}
  fabenv['user']=masternode.properties['ssh_username']
  fabenv['password']=masternode.properties['ssh_password']
  fabenv['key_filename']=masternode.properties['ssh_keyfilename']
  fabenv['host_string']=masternode.properties['ssh_username']+'@'+masternode.properties['ip']
  fabenv['port']=masternode.properties['ssh_port']
  env.update(fabenv)

# utility class to process options in the form
# specific to kubectl
class Option(object):
  def __init__(self,arg,val,cond=None,option_name=None):
    self._arg=arg
    self._option_name=option_name
    self._cond=cond
    self._val=val

  def __str__(self):
    if(self._cond):
      _val_=self._val
      if(not eval(self._cond)):
        return ''
    return "--"+(self._option_name or self._arg)+"="+str(self._val)

def buildopts(kwargs,namedict={},conddict={},flags=[],ignore=[]):
  outstr=''
  for k,v in kwargs.iteritems():
    if(k.startswith('_') or k=='ctx' or k in ignore):
      continue
    if(not v):
      continue
    if(k in conddict):
      _val_=v
      if(not eval(conddict[k])):
        continue
    if(k in namedict):
      outstr=outstr+" --"+namedict[k]
    else:
      outstr=outstr+" --"+k
    if(not k in flags):
      outstr=outstr+"="+str(v)
  return outstr


def get_ip(master):
  if(ctx.local):
    return ctx.get_node(master).properties['ip']
  else:
    raise('not implemented')  # need to get default instance in cloud case

