from cloudify import ctx
from cloudify_rest_client import exceptions as rest_exceptions
import random


mhostkey="mongos_host_{}".format(ctx.target.instance.id)
server="{}:{}".format(ctx.target.instance.host_ip,ctx.target.instance.runtime_properties['mongo_port'])

ctx.logger.info("setting key:{} = {}".format(mhostkey,server))
try:
    ctx.source.instance.runtime_properties['dbhosts']=ctx.target.instance.runtime_properties['dbhosts']
    ctx.source.instance.runtime_properties[mhostkey]=server
    ctx.source.instance.update()
except rest_exceptions.CloudifyClientError as e:
  if 'conflict' in str(e):
    ctx.operation.retry(
      message='Backends updated concurrently, retrying.',
      retry_after=random.randint(1,3))
  else:
    raise

