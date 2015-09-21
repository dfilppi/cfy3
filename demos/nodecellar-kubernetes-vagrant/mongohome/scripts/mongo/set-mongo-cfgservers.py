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
    ctx.source.instance.runtime_properties[rtkey]=server
    ctx.source.instance.update()
except rest_exceptions.CloudifyClientError as e:
  if 'conflict' in str(e):
    ctx.operation.retry(
      message='Backends updated concurrently, retrying.',
      retry_after=random.randint(1,3))
  else:
    raise

ctx.logger.info("  source runtime_properties ===> {}".format(str(ctx.source.instance.runtime_properties)))
