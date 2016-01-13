from cloudify.exceptions import RecoverableError
from cloudify import ctx
from cloudify import exceptions

ctx.source.instance.runtime_properties['mongo_ip']=ctx.target.instance.runtime_properties['mongo_info']['ip']
ctx.source.instance.runtime_properties['mongo_port']=ctx.target.instance.runtime_properties['mongo_info']['port']
