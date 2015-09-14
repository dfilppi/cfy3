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
from cloudify import ctx
from fabric.api import run,env,put
import yaml

# Called when connecting to master.  Gets ip and port
@operation
def connect_master(**kwargs):
  if(ctx._local):
    ctx.source.instance.runtime_properties['master_ip']=ctx.target.node.properties['ip']
  else:
    ctx.source.instance.runtime_properties['master_ip']=ctx.target.instance.runtime_properties['host_ip']
  ctx.source.instance.runtime_properties['master_port']=ctx.target.node.properties['master_port']
  ctx.source.instance.runtime_properties['ssh_username']=ctx.target.node.properties['ssh_username']
  ctx.source.instance.runtime_properties['ssh_password']=ctx.target.node.properties['ssh_password']
  ctx.source.instance.runtime_properties['ssh_port']=ctx.target.node.properties['ssh_port']
  ctx.source.instance.runtime_properties['ssh_keyfilename']=ctx.target.node.properties['ssh_keyfilename']

@operation
def kube_run_expose(**kwargs):
  config=ctx.node.properties['config']
#  ctx.logger.info("-->config={}".format(yaml.safe_dump(ctx.node.properties['config'])))

  fabenv={}
  fabenv['user']=ctx.instance.runtime_properties['ssh_username']
  fabenv['password']=ctx.instance.runtime_properties['ssh_password']
  fabenv['key_filename']=ctx.instance.runtime_properties['ssh_keyfilename']
  fabenv['host_string']=ctx.instance.runtime_properties['ssh_username']+'@'+ctx.instance.runtime_properties['master_ip']
  fabenv['port']=ctx.instance.runtime_properties['ssh_port']
  env.update(fabenv)

  if(config):
    fname="/tmp/kub_{}.yaml".format(ctx.instance.id)
    with open(fname,'w') as f:
      yaml.safe_dump(config,f)
    put(fname,fname)
    cmd="./kubectl -s http://localhost:8080 create -f "+fname

    run(cmd)

  else:
    # do kubectl run
    cmd='./kubectl -s http://localhost:8080 run {} --image={} --port={} --replicas={}'.format(ctx.node.properties['name'],ctx.node.properties['image'],ctx.node.properties['target_port'],ctx.node.properties['replicas'])
    if(ctx.node.properties['run_overrides']):
      cmd=cmd+" --overrides={}".format(ctx.node.properties['run_overrides'])

    run(cmd)

    # do kubectl expose
    cmd='./kubectl -s http://localhost:8080 expose rc {} --port={} --protocol={}'.format(ctx.node.properties['name'],ctx.node.properties['port'],ctx.node.properties['protocol'])
    if(ctx.node.properties['expose_overrides']):
      cmd=cmd+" --overrides={}".format(ctx.node.properties['expose_overrides'])

    run(cmd)
