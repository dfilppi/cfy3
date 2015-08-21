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


# Called when connecting to master.  Gets ip and port
@operation
def connect_master(**kwargs):
  if(ctx._local):
    ctx.source.instance.runtime_properties['master_ip']=ctx.target.node.properties['ip']
  else:
    ctx.source.instance.runtime_properties['master_ip']=ctx.target.instance.runtime_properties['host_ip']
  ctx.source.instance.runtime_properties['master_port']=ctx.target.node.properties['master_port']

