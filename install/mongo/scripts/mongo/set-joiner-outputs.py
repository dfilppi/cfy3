import socket
import time
import subprocess

from pymongo import MongoClient
from cloudify import ctx
from cloudify import utils

##################################################################
# Find config servers and combine into comma separated list
# for easy consumption
##################################################################

cfghosts=""
for key,val in ctx.instance.runtime_properties.iteritems():
  ctx.logger.info("joiner key={}".format(key))
  if ( key.startswith("cfg_server_host")):
    ctx.logger.info(" adding {} to config hosts".format(val))
    cfghosts=cfghosts+val+","

if len(cfghosts)>0:
  cfghosts=cfghosts.rstrip(',')

ctx.instance.runtime_properties['cfghosts']=cfghosts

ctx.logger.info( "Set cfghosts to ({})".format(cfghosts))

##################################################################
# Find mongod servers and combine into comma separated list
# for easy consumption
##################################################################

dbhosts=""
replhosts={}   # save for replset init
for key,val in ctx.instance.runtime_properties.iteritems():
  ctx.logger.info("got key={}".format(key))
  if ( key.startswith("db_server_host_")):
    ctx.logger.info(" adding {} to db hosts".format(val))
    dbhosts=dbhosts+val+","
    h,p,r = val.split(':')
    if(not r in replhosts):
      replhosts[r]=[]
    hp="{}:{}".format(h,p)
    ctx.logger.info(" adding {} to replicasets cache".format(hp))
    replhosts[r].append(hp)

if len(dbhosts)>0:
  dbhosts=dbhosts.rstrip(',')

ctx.instance.runtime_properties['dbhosts']=dbhosts

ctx.logger.info( "Set dbhosts to ({})".format(dbhosts))


##################################################################
# Initialize replica sets
##################################################################

# for each replicaset

ctx.logger.info( "replosts size:{}".format(len(replhosts)))
for k,v in replhosts.iteritems():
  ctx.logger.info( "replhost:{}".format(key))
  if(len(v)>0):
    config={'_id': k, 'members': []}
    for i,h in enumerate(v):
      config['members'].append({'_id':i,'host':h})
    h,p=v[0].split(":")
    c=MongoClient(h,int(p))
    ctx.logger.info("initiating replicaset:{}".format(str(config)))
    try:
      c.admin.command("replSetInitiate",config)
    except:
      pass
    c.close()
