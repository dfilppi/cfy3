# coding=utf-8

"""

Custom collector to return number of connections on port. Suitable for
demos only

"""

import diamond.collector
import datetime
import subprocess
import re


class ConnCollector(diamond.collector.Collector):

    def get_default_config_help(self):
        config_help = super(ConnCollector, self).get_default_config_help()
        config_help.update({
        })
        return config_help

    def get_default_config(self):
        default_config = super(ConnCollector, self).get_default_config()
        default_config['port'] = 3000
        default_config['path'] = ''
        return default_config


    def _get_conns(self,port):
      sub=subprocess.check_output(['/bin/netstat','-pnat'])

      cnt=0
      for line in sub.split('\n'):
        if line:
          m=re.match("tcp[\s]+[\S]+[\s]+[\S]+[\s]+[^:]+:([\d]+).*",line)
          if(m and int(m.group(1))==port):
            cnt=cnt+1
      return cnt

    def collect(self):
         self.log.debug("collecting connections on port ", str(self.config['port']))
         #req_start = datetime.datetime.now()
         try:
             # build a compatible name : no '.' and no'/' in the name
             metric_name = "connections"

             conncnt=self._get_conns(int(self.config['port']))
             self.log.debug("collected %d", conncnt)
             self.publish_gauge(
                 metric_name,
                 float(conncnt))

         except Exception, e:
             self.log.error("Exception: %s", e)
