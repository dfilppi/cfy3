from cloudify import ctx


# get the mongocfg hosts from the proxy
ctx.logger.info("Setting cfghosts from proxy: {}".format(str(ctx.target.instance.runtime_properties['outputs']['cluster_info']['cfghosts'])))

ctx.source.instance.runtime_properties['cfghosts']=ctx.target.instance.runtime_properties['outputs']['cluster_info']['cfghosts']
ctx.source.instance.runtime_properties['dbhosts']=ctx.target.instance.runtime_properties['outputs']['cluster_info']['dbhosts']
