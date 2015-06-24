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

import time
import sys

# ctx is imported and used in operations
from cloudify import ctx,utils,manager
from cloudify.exceptions import NonRecoverableError,RecoverableError

from cloudify.decorators import operation

@operation
def wait(**kwargs):

    # check args
    if(not 'deployment_id' in ctx.node.properties):
      raise NonRecoverableError("deployment id not specified for proxy")
    if(not 'wait_for' in ctx.node.properties or
        (ctx.node.properties['wait_for']!='exists' and
         ctx.node.properties['wait_for']!='expr')):
      raise NonRecoverableError("deployment id not specified for proxy")

    client=manager.get_rest_client()
    timeout=ctx.node.properties['timeout']
    start=time.time()

    endtime=start+timeout

    # handle "exists"
    if(ctx.node.properties['wait_for']=='exists'):
      while(time.time()<=endtime):
        try:

          val=manager.get_rest_client().deployments.outputs.get(ctx.node.properties['deployment_id']).outputs[ctx.node.properties['test']]

          if(val!=None):
            ctx.instance.runtime_properties['outputs'] = manager.get_rest_client().deployments.outputs.get(ctx.node.properties['deployment_id']).outputs
            return
        except:
          ctx.logger.info("caught exception {0}".format(sys.exc_info()[0]))
          pass
        time.sleep(5)

    # handle "expr"
    elif(ctx.node.properties['wait_for']=='expr'):
      while(time.time()<=endtime):
        try:
          outputs=manager.get_rest_client().deployments.outputs.get(ctx.node.properties['deployment_id']).outputs

          ctx.logger.info("evaluating {0}".format(ctx.node.properties['test']))
          if(eval(ctx.node.properties['test'])==True):
            ctx.logger.info("evaluated as True")
            ctx.instance.runtime_properties['outputs']=outputs
            return
          else:
            ctx.logger.info("evaluated as False")
      
        except:
          ctx.logger.info("caught exception {0}".format(sys.exc_info()[0]))
        time.sleep(5)
  
    raise RecoverableError("timed out waiting for deployment")
