from cloudify import ctx
from cloudify_rest_client import exceptions as rest_exceptions
from cloudify.exceptions import RecoverableError
import time
import random


nhostkey="node_host_{}".format(ctx.target.instance.id)
server="{}".format(ctx.target.instance.runtime_properties.floating_ip_address)

ctx.logger.info("setting key:{} = {}".format(nhostkey,server))
try:
  for i in range(10):
    ctx.source.instance.runtime_properties[nhostkey]=server
    ctx.source.instance.update()
    if(nhostkey in ctx.source.instance.runtime_properties):
      break
    ctx.logger.info(" props update ignored, retrying")
    time.sleep(random.uniform(.1,1.0))
except rest_exceptions.CloudifyClientError as e:
  if 'conflict' in str(e):
    time.sleep(random.uniform(.1,1.0))  #random sleep to avoid sync race
    raise RecoverableError('conflict updating runtime_properties')
  else:
    raise

