from cloudify import ctx
from cloudify_rest_client import exceptions as rest_exceptions
from cloudify.exceptions import RecoverableError
import time
import random


mhostkey="mongos_host_{}".format(ctx.target.instance.id)
server="{}:{}".format(ctx.target.instance.host_ip,ctx.target.instance.runtime_properties['mongo_port'])

ctx.logger.info("setting key:{} = {}".format(mhostkey,server))
try:
  for i in range(10):
    ctx.source.instance.runtime_properties['dbhosts']=ctx.target.instance.runtime_properties['dbhosts']
    ctx.source.instance.runtime_properties[mhostkey]=server
    ctx.source.instance.update()
    if(mhostkey in ctx.source.instance.runtime_properties and 'dbhosts' in ctx.source.instance.runtime_properties):
      break
    ctx.logger.info(" props update ignored, retrying")
    time.sleep(random.uniform(.1,1.0))
except rest_exceptions.CloudifyClientError as e:
  if 'conflict' in str(e):
    time.sleep(random.uniform(.1,1.0))  #random sleep to avoid sync race
    raise RecoverableError('conflict updating runtime_properties')
  else:
    raise

