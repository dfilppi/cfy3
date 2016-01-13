from configobj import ConfigObj
import os

# Relevant env vars
#
# CC_HTTP_URL    - modified nodecellar url
# 
#
# CH_SERVER      - cloudify manager ip/host
# CH_PORT        - rabbit port
# CH_USER        - rabbit user
# CH_PASSWORD    - rabbit pwd
#
#Configure

ip = os.popen('ifconfig eth0 | grep "inet\ addr" | cut -d: -f2 | cut -d" " -f1').read().rstrip()
ip=ip.replace('.','_')

cfg=ConfigObj("/diamond/diamond.conf",list_values=False)
cfg['collectors']['HttpCollector']['enabled']="true"
cfg['collectors']['HttpCollector']['req_url']=[os.getenv("CC_HTTP_URL")]
cfg['collectors']['HttpCollector']['hostname']='.'.join([ip,os.getenv("CC_NODE"),os.getenv("CC_INSTANCE")])
cfg['collectors']['HttpCollector']['path_prefix']=os.getenv("CC_DEPLOYMENT")

cfg['handlers']['CloudifyHandler']['server']=os.getenv('CH_SERVER')
cfg['handlers']['CloudifyHandler']['port']=os.getenv('CH_PORT',5672)
cfg['handlers']['CloudifyHandler']['user']=os.getenv('CH_USER','cloudify')
cfg['handlers']['CloudifyHandler']['password']=os.getenv('CH_PASSWORD','c10udify')
cfg.write()

