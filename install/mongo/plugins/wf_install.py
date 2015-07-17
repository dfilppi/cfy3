from cloudify.workflows import ctx, parameters as inputs
import cloudify.utils as utils
import requests
import json

# Elasticsearch port=9200
ESPORT=9200
mgr_ip='127.0.0.1'
try:
  mgr_ip=utils.get_manager_ip()
except:
  pass

ctx.logger.info("mgrip={}".format(mgr_ip))

esurl="http://{}:{}/".format(mgr_ip,ESPORT)

r=requests.get(esurl)
if r.status_code != 200:
  raise "elasticsearch not found at {}:{}".format(mgr_ip,ESPORT)



node = next(ctx.nodes)
ctx.logger.info("node id={}".format(node.id))
instance = next(node.instances)
#instance.execute_operation('test.op', kwargs={
    #'service': inputs.service,
    #'metric': inputs.metric
#})


payload={'message':'my test document'}
r=requests.post(esurl+"myindex/mytype",data=json.dumps(payload))
ctx.logger.info(r.text)
#r=requests.get("{}_aliases?pretty=1".format(esurl,mgr_ip,ESPORT))
r=requests.get("{}".format(esurl+"myindex/mytype/_search?",mgr_ip,ESPORT))
ctx.logger.info(r.json())

