from cloudify_rest_client import exceptions as rest_exceptions
from cloudify.exceptions import RecoverableError
from cloudify import ctx
import time
import random

ctx.logger.info(str(ctx.target.instance.runtime_properties))

rtkey="cfg_server_host_{}".format(ctx.target.instance.id)
server="{}:{}".format(ctx.target.instance.host_ip,ctx.target.instance.runtime_properties['mongo_port'])

ctx.logger.info("setting key:{} = {}".format(rtkey,server))

try:
  for i in range(10):
    ctx.source.instance.runtime_properties[rtkey]=server
    ctx.source.instance.update()
    if(rtkey in ctx.source.instance.runtime_properties):
      break
    ctx.logger.info(" rt props update ignored, retrying")
    time.sleep(random.uniform(.1,1.0))
except rest_exceptions.CloudifyClientError as e:
  if 'conflict' in str(e):
    time.sleep(random.uniform(.1,1.0))  #random sleep to avoid sync race
    raise RecoverableError('conflict updating runtime_properties')
  else:
    raise

ctx.logger.info("  source runtime_properties ===> {}".format(str(ctx.source.instance.runtime_properties)))
