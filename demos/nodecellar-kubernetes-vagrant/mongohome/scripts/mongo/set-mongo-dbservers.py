from cloudify_rest_client import exceptions as rest_exceptions
from cloudify.exceptions import RecoverableError
from cloudify import ctx
import time
import random
from cloudify import exceptions

ctx.logger.info("dbserver rtprops={}".format(str(ctx.target.instance.runtime_properties)))

rtkey="db_server_host_{}".format(ctx.target.instance.id)
rtval="{}:{}:{}".format(ctx.target.instance.host_ip,ctx.target.instance.runtime_properties['mongo_port'],ctx.target.instance.runtime_properties['replicaset_name'])

ctx.logger.info("setting key:{} = {}".format(rtkey,rtval))
try:
  ctx.source.instance.runtime_properties[rtkey]=rtval
  ctx.source.instance.update()
except rest_exceptions.CloudifyClientError as e:
  if 'conflict' in str(e):
    ctx.operation.retry(
      message='Backends updated concurrently, retrying.',
      retry_after=random.randint(1,3))
  else:
    raise
 
