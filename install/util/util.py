########
# Copyright (c) 2014 GigaSpaces Technologies Ltd. All rights reserved
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
#    * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    * See the License for the specific language governing permissions and
#    * limitations under the License.

import time
import requests
import json
import sys

#
# Return node instances that have been started
#
def _instances_started(hist):
  if(hist==None):
    raise "null hist supplied"
  started={}
  
  for event in hist.history:
    if(event.step == 'start' and event.status == 'success'):
      started[event.instance_id]=event

  return started  

#
# Return completed tasks for instance id
#
def _completed_tasks(hist,instance_id): 
  completed={}
  for event in hist.history:
    if(event.instance_id==instance_id):
      if(event.status=="success"):
        completed[event.step]=event

  return completed
  

#
# Represents an ElasticSearch connection.  Only operates on the
# install index
#
class ES(object):

  def __init__(self,mgr_ip):
    self._esurl=''
    ESPORT=9200

    self._esurl="http://{}:{}/".format(mgr_ip,ESPORT)

    r=requests.get(self._esurl)
    if r.status_code != 200:
      raise "elasticsearch not found at {}:{}".format(mgr_ip,ESPORT)


  def get(self,path,payload=None):
    if(payload):
      response=requests.get(self._esurl+"install/"+path,data=json.dumps(payload))
    else:
      response=requests.get(self._esurl+"install/"+path)
    return response

  def post(self,path,payload):
    response=requests.post(self._esurl+"install/"+path,data=json.dumps(payload))
    return response

  def delete(self,path):
    return requests.delete(self._esurl+"install/"+path)
#
# Get an install history
#
class InstallHistory(object):
  def __init__(self,did,mgr_ip):
    self._did=did
    self._es=ES(mgr_ip)
    self._get_history()
    self._history=self._get_history()

  def _get_history(self):
    hist=self._es.get("{}/_search?size=1000000".format(self._did)).json()
    self._history=[]
    if('hits' in hist and 'hits' in hist['hits']):
      for hit in hist['hits']['hits']:
        self._history.append(InstallEvent(hit))
    return self._history

  @property
  def history(self):
    return self._history

  @property
  def hit_count(self):
    return len(self._history)


class InstallEvent(object):
  #the 'hit' arg is json response from ES
  def __init__(self,hit):
    self._id=hit['_id']
    self._deployment_id=hit['_source']['deployment_id']
    self._status=hit['_source']['status']
    self._task_id=hit['_source']['task_id']
    self._node_id=hit['_source']['node_id']
    self._instance_id=hit['_source']['instance_id']
    self._step=hit['_source']['step']
    self._time=hit['_source']['time']

  @property
  def id(self):
    return self._id

  @property
  def deployment_id(self):
    return self._deployment_id

  @property
  def status(self):
    return self._status

  @property
  def task_id(self):
    return self._task_id

  @property
  def node_id(self):
    return self._node_id

  @property
  def instance_id(self):
    return self._instance_id

  @property
  def step(self):
    return self._step

  @property
  def time(self):
    return self._time



#ih=InstallHistory('md','15.125.83.39')
ih=InstallHistory(sys.argv[2],sys.argv[1])

for i in _instances_started(ih):
  for t in _completed_tasks(ih,i):
    print "instance: %25.25s  complete task: %10s" % (i,t)
