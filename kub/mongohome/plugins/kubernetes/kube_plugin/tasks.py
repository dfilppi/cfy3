########
# Copyright (c) 2015 GigaSpaces Technologies Ltd. All rights reserved
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
#    * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    * See the License for the specific language governing permissions and
#    * limitations under the License.

#
# Kubernetes plugin implementation
#
from cloudify.decorators import operation
from cloudify import ctx,manager,utils
import os
import re
import time
import subprocess
import yaml

# Called when connecting to master.  Gets ip and port
@operation
def connect_master(**kwargs):
  ctx.logger.info("in connect_master")
  ctx.target.node._get_node_if_needed()
  if(ctx._local):
    ctx.logger.info("running local mode")
    ctx.source.instance.runtime_properties['master_ip']=ctx.target.node.properties['ip']
  elif(ctx.target.node._node.type=='cloudify.kubernetes.Master'):
    ctx.logger.info("connecting to master node")
    ctx.source.instance.runtime_properties['master_ip']=ctx.target.instance.runtime_properties['ip']
    #following properties ignored for non-fabric operation
    ctx.source.instance.runtime_properties['master_port']=ctx.target.node.properties['master_port']
    ctx.source.instance.runtime_properties['ssh_username']=ctx.target.node.properties['ssh_username']
    ctx.source.instance.runtime_properties['ssh_password']=ctx.target.node.properties['ssh_password']
    ctx.source.instance.runtime_properties['ssh_port']=ctx.target.node.properties['ssh_port']
    ctx.source.instance.runtime_properties['ssh_keyfilename']=ctx.target.node.properties['ssh_keyfilename']
  elif(ctx.target.node._node.type=='cloudify.nodes.DeploymentProxy'):
    ctx.logger.info("connecting to dproxy")
    ctx.logger.info("got dproxy url:"+ctx.target.instance.runtime_properties['kubernetes_info']['url'])
    ctx.source.instance.runtime_properties['master_ip']=ctx.target.instance.runtime_properties['kubernetes_info']['url'].split(':')[0]
    ctx.source.instance.runtime_properties['master_port']=ctx.target.instance.runtime_properties['kubernetes_info']['url'].split(':')[1]
  else:
    raise(NonRecoverableError('unsupported relationship'))

# called to connect to a deployment proxy.  generalization of connect_master
@operation
def connect_proxy(**kwargs):
  if (ctx.target.node._node.type!='cloudify.nodes.DeploymentProxy'):
    raise (NonRecoverableError('must connect to DeploymentProxy type'))

  for output in ctx.target.node.properties['inherit_outputs']:
    ctx.source.instance.runtime_properties[output]=ctx.target.instance.runtime_properties[output]
    
@operation
def contained_in(**kwargs):
  ctx.source.instance.runtime_properties['ip']=ctx.target.instance.runtime_properties['ip']

@operation
def copy_rtprops(**kwargs):
  if (not "prop_list" in kwargs or kwargs["prop_list"]==""):
    return
  for prop in kwargs['prop_list'].split(','):
    if(prop in ctx.target.instance.runtime_properties):
      ctx.source.instance.runtime_properties[prop]=ctx.target.instance.runtime_properties[prop]
    
#
# Perform substitutions in overrides
#
def process_subs(s):

  with open("/tmp/subs","a+") as f:
    f.write("processing "+s)

  pat='@{([^}]+)}|%{([^}]+)}'
  client=None
  m=re.search(pat,s)

  with open("/tmp/subs","a+") as f:
    f.write(" m "+str(m)+"\n")

  if(not m):
    #no patterns found
    ctx.logger.info('no pattern found:{}'.format(s))
    return s;
  while(m):

    # Match @ syntax.  Gets runtime properties
    if(m.group(1)):
      with open("/tmp/subs","a+") as f:
        f.write(" m.group(1)="+str(m.group(1))+"\n")
      fields=m.group(1).split(',')
      if m and len(fields)>1:
        # do substitution
        if(not client):
          client=manager.get_rest_client()
        instances=client.node_instances.list(deployment_id=ctx.deployment.id,node_name=fields[0])
        if(instances and len(instances)):
          #just use first instance if more than one
          val=instances[0].runtime_properties
          for field in fields[1:]:
            field=field.strip()
            val=val[field]    #handle nested maps
  
          s=s[:m.start()]+str(val)+s[m.end(1)+1:]
          m=re.search(pat,s)
        else:
          raise Exception("no instances found for node: {}".format(fields[0]))
      else:
        raise Exception("invalid pattern: "+s)

    # Match % syntax.  Gets context property.
    # also handles special token "management_ip"
    elif(m.group(2)):
      with open("/tmp/subs","a+") as f:
        f.write("m.group(2)="+str(m.group(2))+"\n")
      if(m.group(2)=="management_ip"):
        s=s[:m.start()]+str(utils.get_manager_ip())+s[m.end(2)+1:]
      else:
        s=s[:m.start()]+str(eval("ctx."+m.group(2)))+s[m.end(2)+1:]
      m=re.search(pat,s)
      
  return s

#
# Use kubectl to run and expose a service
#
@operation
def kube_run_expose(**kwargs):
  ctx.logger.info("in kube_run_expose")
  config=ctx.node.properties['config']
  config_files=ctx.node.properties['config_files']

  def write_and_run(d):
    os.chdir(os.path.expanduser("~"))
    fname="/tmp/kub_{}.yaml".format(ctx.instance.id)
    with open(fname,'w') as f:
      yaml.safe_dump(d,f)
    cmd="./kubectl -s http://localhost:8080 create -f "+fname + " >> /tmp/kubectl.out 2>&1"
    ctx.logger.info("running create: {}".format(cmd))

    #retry a few times
    retry=0
    while subprocess.call(cmd,shell=True):
      if retry>3:
        raise Exception("couldn't connect to server on 8080")
      retry=retry+1
      ctx.logger.info("run failed retrying")
      time.sleep(2)

  if(config):
    write_and_run(config)
  elif(len(config_files)):
    for file in config_files:
      if (not ctx._local):
        local_path=ctx.download_resource(file['file'])
      else:
        local_path=file['file']
      with open(local_path) as f:
        base=yaml.load(f)
      if('overrides' in file):
        for o in file['overrides']:
          ctx.logger.info("exeing o={}".format(o))
          #check for substitutions
          o=process_subs(o)
          exec "base"+o in globals(),locals()
      write_and_run(base)
  else:
    # do kubectl run
    cmd='./kubectl -s http://localhost:8080 run {} --image={} --port={} --replicas={}'.format(ctx.node.properties['name'],ctx.node.properties['image'],ctx.node.properties['target_port'],ctx.node.properties['replicas'])
    if(ctx.node.properties['run_overrides']):
      cmd=cmd+" --overrides={}".format(ctx.node.properties['run_overrides'])

    subprocess.call(cmd,True)

    # do kubectl expose
    cmd='./kubectl -s http://localhost:8080 expose rc {} --port={} --protocol={}'.format(ctx.node.properties['name'],ctx.node.properties['port'],ctx.node.properties['protocol'])
    if(ctx.node.properties['expose_overrides']):
      cmd=cmd+" --overrides={}".format(ctx.node.properties['expose_overrides'])

    subprocess.call(cmd,shell=True)
