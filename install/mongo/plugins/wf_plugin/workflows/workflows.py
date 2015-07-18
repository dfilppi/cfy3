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

from cloudify.decorators import workflow
from cloudify.workflows.tasks_graph import forkjoin
from cloudify.workflows import tasks as workflow_tasks
import time
import requests
import json


def _get_all_nodes_instances(ctx):
    node_instances = set()
    for node in ctx.nodes:
        for instance in node.instances:
            node_instances.add(instance)
    return node_instances


class InstallationTasksReferences(object):
    def __init__(self):
        self.send_event_creating = {}
        self.set_state_creating = {}
        self.set_state_started = {}


class NodeInstallationTasksSequenceCreator(object):
    """
    This class is used to create a tasks sequence installing one node instance.
    Considering the order of tasks executions, it enforces the proper
    dependencies only in context of this particular node instance.
    """
    def __init__(self,ctx=None):
      self._ctx=ctx


    def create(self, instance, graph, installation_tasks):
        """
        :param installation_tasks: instance of InstallationTasksReferences
        :param instance: node instance to generate the installation tasks for
        """
        sequence = graph.sequence()
        sequence.add(instance.set_state('initializing'))
        sequence.add(
            forkjoin(
                installation_tasks.set_state_creating[instance.id],
                installation_tasks.send_event_creating[instance.id]
            ))

        sequence.add(_add_es_log(self._ctx,instance,'create',instance.execute_operation('cloudify.interfaces.lifecycle.create')))
        sequence.add(instance.set_state('created'))
        sequence.add(
            forkjoin(*_relationship_operations(
                instance,
                'cloudify.interfaces.relationship_lifecycle.preconfigure'
            )))
        sequence.add(
            forkjoin(
                instance.set_state('configuring'),
                instance.send_event('Configuring node')
            ))
        sequence.add(_add_es_log(self._ctx,instance,'configure',instance.execute_operation('cloudify.interfaces.lifecycle.configure')))
        sequence.add(instance.set_state('configured'))
        sequence.add(
            forkjoin(*_relationship_operations(
                instance,
                'cloudify.interfaces.relationship_lifecycle.postconfigure'
            )))
        sequence.add(forkjoin(
                instance.set_state('starting'),
                instance.send_event('Starting node')
            ))
        sequence.add(_add_es_log(self._ctx,instance,'start',instance.execute_operation('cloudify.interfaces.lifecycle.start')))

        # If this is a host node, we need to add specific host start
        # tasks such as waiting for it to start and installing the agent
        # worker (if necessary)
        if _is_host_node(instance):
            sequence.add(*_host_post_start(instance))

        sequence.add(
            forkjoin(
                instance.execute_operation(
                    'cloudify.interfaces.monitoring.start'),
                *_relationship_operations(
                    instance,
                    'cloudify.interfaces.relationship_lifecycle.establish'
                )),
            installation_tasks.set_state_started[instance.id])


class InstallationTasksGraphFinisher(object):
    def __init__(self, graph, node_instances, intact_nodes, tasks):
        self.graph = graph
        self.node_instances = node_instances
        self.intact_nodes = intact_nodes
        self.tasks = tasks

    def _enforce_correct_src_trg_order(self, instance, rel):
        """
        make a dependency between the create tasks (event, state)
        and the started state task of the target
        """
        target_set_started = self.tasks.set_state_started[rel.target_id]
        node_set_creating = self.tasks.set_state_creating[instance.id]
        node_event_creating = self.tasks.send_event_creating[instance.id]
        self.graph.add_dependency(node_set_creating, target_set_started)
        self.graph.add_dependency(node_event_creating, target_set_started)

    def finish_creation(self):
        # Create task dependencies based on node relationships
        for instance in self.node_instances:
            for rel in instance.relationships:
                self._enforce_correct_src_trg_order(instance, rel)


class RuntimeInstallationTasksGraphFinisher(InstallationTasksGraphFinisher):
    def _enforce_correct_src_trg_order(self, instance, rel):
        # Handle only nodes within self.node_instances, others are running
        if rel.target_node_instance in self.node_instances:
            super(RuntimeInstallationTasksGraphFinisher,
                  self)._enforce_correct_src_trg_order(instance, rel)

    def finish_creation(self):
        super(RuntimeInstallationTasksGraphFinisher, self).finish_creation()
        # Add operations for intact nodes depending on a node instance
        # belonging to node_instances (which are being reinstalled)
        for instance in self.intact_nodes:
            for rel in instance.relationships:
                if rel.target_node_instance in self.node_instances:
                    trg_started = self.tasks.set_state_started[rel.target_id]
                    establish_ops = _relationship_operations_with_target(
                        rel,
                        'cloudify.interfaces.relationship_lifecycle.establish')
                    for establish_op, _ in establish_ops:
                        self.graph.add_task(establish_op)
                        self.graph.add_dependency(establish_op, trg_started)


def _install_node_instances(ctx, node_instances, intact_nodes,
                            node_tasks_seq_creator, graph_finisher_cls,resume):

    # switch to graph mode (operations on the context return tasks instead of
    # result instances)
    graph = ctx.graph_mode()

    # We need reference to the create event/state tasks and the started
    # task so we can later create a proper dependency between nodes and
    # their relationships. We use the below tasks as part of a single node
    # workflow, and to create the dependency (at the bottom)
    tasks = InstallationTasksReferences()
    for instance in node_instances:
        tasks.send_event_creating[instance.id] = instance.send_event(
            'Creating node')
        tasks.set_state_creating[instance.id] = instance.set_state('creating')
        tasks.set_state_started[instance.id] = instance.set_state('started')

    # Create node linear task sequences
    # For each node, we create a "task sequence" in which all tasks
    # added to it will be executed in a sequential manner
    for instance in node_instances:
        node_tasks_seq_creator.create(instance, graph, tasks)

    graph_finisher_cls(
        graph,
        node_instances,
        intact_nodes,
        tasks
    ).finish_creation()

    graph.execute()


class UninstallationTasksReferences(object):
    def __init__(self):
        self.set_state_stopping = {}
        self.set_state_deleted = {}
        self.stop_node = {}
        self.stop_monitor = {}
        self.delete_node = {}


class NodeUninstallationTasksSequenceCreator(object):
    def create(self, instance, graph, uninstallation_tasks):
        unlink_tasks_with_target_ids = _relationship_operations_with_targets(
            instance, 'cloudify.interfaces.relationship_lifecycle.unlink')

        sequence = graph.sequence()
        sequence.add(
            uninstallation_tasks.set_state_stopping[instance.id],
            instance.send_event('Stopping node')
        )
        if _is_host_node(instance):
            sequence.add(*_host_pre_stop(instance))
        sequence.add(
            uninstallation_tasks.stop_node[instance.id],
            instance.set_state('stopped'),
            forkjoin(*[task for task, _ in unlink_tasks_with_target_ids]),
            instance.set_state('deleting'),
            instance.send_event('Deleting node'),
            uninstallation_tasks.delete_node[instance.id],
            uninstallation_tasks.set_state_deleted[instance.id]
        )

        # adding the stop monitor task not as a part of the sequence,
        # as it can happen in parallel with any other task, and is only
        # dependent on the set node state 'stopping' task
        graph.add_task(uninstallation_tasks.stop_monitor[instance.id])
        graph.add_dependency(
            uninstallation_tasks.stop_monitor[instance.id],
            uninstallation_tasks.set_state_stopping[instance.id]
        )

        # augmenting the stop node, stop monitor and delete node tasks with
        # error handlers
        _set_send_node_event_on_error_handler(
            uninstallation_tasks.stop_node[instance.id],
            instance,
            "Error occurred while stopping node - ignoring...")
        _set_send_node_event_on_error_handler(
            uninstallation_tasks.stop_monitor[instance.id],
            instance,
            "Error occurred while stopping monitor - ignoring...")
        _set_send_node_event_on_error_handler(
            uninstallation_tasks.delete_node[instance.id],
            instance,
            "Error occurred while deleting node - ignoring...")
        _set_send_node_evt_on_failed_unlink_handlers(
            instance,
            unlink_tasks_with_target_ids)


class UninstallationTasksGraphFinisher(object):
    def __init__(self, graph, node_instances, intact_nodes, tasks):
        self.graph = graph
        self.node_instances = node_instances
        self.intact_nodes = intact_nodes
        self.tasks = tasks

    def _enforce_correct_src_trg_order(self, instance, rel):
        """
        make a dependency between the target's stopping task
        and the deleted state task of the current node
        """
        self.graph.add_dependency(
            self.tasks.set_state_stopping[rel.target_id],
            self.tasks.set_state_deleted[instance.id]
        )

    def finish_creation(self):
        # Create task dependencies based on node relationships
        for instance in self.node_instances:
            for rel in instance.relationships:
                self._enforce_correct_src_trg_order(instance, rel)


class RuntimeUninstallationTasksGraphFinisher(
        UninstallationTasksGraphFinisher):

    def _enforce_correct_src_trg_order(self, instance, rel):
        if rel.target_node_instance in self.node_instances:
            super(RuntimeUninstallationTasksGraphFinisher,
                  self)._enforce_correct_src_trg_order(instance, rel)

    def finish_creation(self):
        super(RuntimeUninstallationTasksGraphFinisher, self).finish_creation()
        for instance in self.intact_nodes:
            for rel in instance.relationships:
                if rel.target_node_instance in self.node_instances:
                    target_stopped = self.tasks.stop_node[rel.target_id]
                    unlink_tasks = _relationship_operations_with_target(
                        rel,
                        'cloudify.interfaces.relationship_lifecycle.unlink')
                    for unlink_task, _ in unlink_tasks:
                        self.graph.add_task(unlink_task)
                        self.graph.add_dependency(unlink_task, target_stopped)
                    _set_send_node_evt_on_failed_unlink_handlers(
                        instance, unlink_tasks)


def _uninstall_node_instances(ctx, node_instances, intact_nodes,
                              node_tasks_seq_creator, graph_finisher_cls,
                              graph=None):
    if not graph:
        # switch to graph mode (operations on the context return tasks instead
        # of result instances)
        graph = ctx.graph_mode()
    tasks_refs = UninstallationTasksReferences()
    for instance in node_instances:
        # We need reference to the set deleted state tasks and the set
        # stopping state tasks so we can later create a proper dependency
        # between nodes and their relationships. We use the below tasks as
        # part of a single node workflow, and to create the dependency
        # (at the bottom)
        tasks_refs.set_state_stopping[instance.id] = instance.set_state(
            'stopping')
        tasks_refs.set_state_deleted[instance.id] = instance.set_state(
            'deleted')

        # We need reference to the stop node tasks, stop monitor tasks and
        # delete node tasks as we augment them with on_failure error
        # handlers later on
        tasks_refs.stop_node[instance.id] = instance.execute_operation(
            'cloudify.interfaces.lifecycle.stop')
        tasks_refs.stop_monitor[instance.id] = instance.execute_operation(
            'cloudify.interfaces.monitoring.stop')
        tasks_refs.delete_node[instance.id] = instance.execute_operation(
            'cloudify.interfaces.lifecycle.delete')

    # Create node linear task sequences
    # For each node, we create a "task sequence" in which all tasks
    # added to it will be executed in a sequential manner
    for instance in node_instances:
        node_tasks_seq_creator.create(instance, graph, tasks_refs)

    graph_finisher_cls(
        graph,
        node_instances,
        intact_nodes,
        tasks_refs
    ).finish_creation()

    graph.execute()


def _set_send_node_event_on_error_handler(task, node_instance, error_message):
    def send_node_event_error_handler(tsk):
        node_instance.send_event(error_message)
        return workflow_tasks.HandlerResult.ignore()
    task.on_failure = send_node_event_error_handler


def _set_send_node_evt_on_failed_unlink_handlers(instance, tasks_with_targets):
    for unlink_task, target_id in tasks_with_targets:
        _set_send_node_event_on_error_handler(
            unlink_task,
            instance,
            "Error occurred while unlinking node from node {0} - "
            "ignoring...".format(target_id)
        )


def _relationship_operations(node_instance, operation):
    tasks_with_targets = _relationship_operations_with_targets(
        node_instance, operation)
    return [task for task, _ in tasks_with_targets]


def _relationship_operations_with_targets(node_instance, operation):
    tasks = []
    for relationship in node_instance.relationships:
        tasks += _relationship_operations_with_target(relationship, operation)
    return tasks


def _relationship_operations_with_target(relationship, operation):
    
    return [
        (relationship.execute_source_operation(operation),
         relationship.target_id),
        (relationship.execute_target_operation(operation),
         relationship.target_id)
    ]


def _is_host_node(node_instance):
    return 'cloudify.nodes.Compute' in node_instance.node.type_hierarchy


def _wait_for_host_to_start(host_node_instance):
    task = host_node_instance.execute_operation(
        'cloudify.interfaces.host.get_state')

    # handler returns True if if get_state returns False,
    # this means, that get_state will be re-executed until
    
    # get_state returns True
    def node_get_state_handler(tsk):
        host_started = tsk.async_result.get()
        if host_started:
            return workflow_tasks.HandlerResult.cont()
        else:
            return workflow_tasks.HandlerResult.retry(
                ignore_total_retries=True)
    if not task.is_nop():
        task.on_success = node_get_state_handler
    return task


def _host_post_start(host_node_instance):

    plugins_to_install = filter(lambda plugin: plugin['install'],
                                host_node_instance.node.plugins_to_install)

    tasks = [_wait_for_host_to_start(host_node_instance)]
    if host_node_instance.node.properties['install_agent'] is True:
        tasks += [
            host_node_instance.send_event('Installing worker'),
            host_node_instance.execute_operation(
                'cloudify.interfaces.worker_installer.install'),
            host_node_instance.execute_operation(
                'cloudify.interfaces.worker_installer.start'),
        ]
        if plugins_to_install:
            tasks += [
                host_node_instance.send_event('Installing host plugins'),
                host_node_instance.execute_operation(
                    'cloudify.interfaces.plugin_installer.install',
                    kwargs={
                        'plugins': plugins_to_install}),
                host_node_instance.execute_operation(
                    'cloudify.interfaces.worker_installer.restart',
                    send_task_events=False)
            ]
    tasks += [
        host_node_instance.execute_operation(
            'cloudify.interfaces.monitoring_agent.install'),
        host_node_instance.execute_operation(
            'cloudify.interfaces.monitoring_agent.start'),
    ]
    return tasks


def _host_pre_stop(host_node_instance):
    tasks = []
    tasks += [
        host_node_instance.execute_operation(
            'cloudify.interfaces.monitoring_agent.stop'),
        host_node_instance.execute_operation(
            'cloudify.interfaces.monitoring_agent.uninstall'),
    ]
    if host_node_instance.node.properties['install_agent'] is True:
        tasks += [
            host_node_instance.send_event('Uninstalling worker'),
            host_node_instance.execute_operation(
                'cloudify.interfaces.worker_installer.stop'),
            host_node_instance.execute_operation(
                'cloudify.interfaces.worker_installer.uninstall')
        ]

    for task in tasks:
        if task.is_remote():
            _set_send_node_event_on_error_handler(
                task, host_node_instance,
                'Error occurred while uninstalling worker - ignoring...')

    return tasks


@workflow
def install(ctx, **kwargs):
    """Default install workflow"""

    _install_node_instances(
        ctx,
        _get_all_nodes_instances(ctx),
        set(),
        NodeInstallationTasksSequenceCreator(ctx),
        InstallationTasksGraphFinisher,
        kwargs['resume']
    )


@workflow
def auto_heal_reinstall_node_subgraph(
        ctx,
        node_instance_id,
        diagnose_value='Not provided',
        **kwargs):
    """Reinstalls the whole subgraph of the system topology

    The subgraph consists of all the nodes that are hosted in the
    failing node's compute and the compute itself.
    Additionally it unlinks and establishes appropriate relationships

    :param ctx: cloudify context
    :param node_id: failing node's id
    :param diagnose_value: diagnosed reason of failure
    """

    ctx.logger.info("Starting 'heal' workflow on {0}, Diagnosis: {1}"
                    .format(node_instance_id, diagnose_value))
    failing_node = ctx.get_node_instance(node_instance_id)
    failing_node_host = ctx.get_node_instance(
        failing_node._node_instance.host_id
    )
    subgraph_node_instances = failing_node_host.get_contained_subgraph()
    intact_nodes = _get_all_nodes_instances(ctx) - subgraph_node_instances
    _uninstall_node_instances(
        ctx,
        subgraph_node_instances,
        intact_nodes,
        NodeUninstallationTasksSequenceCreator(),
        RuntimeUninstallationTasksGraphFinisher
    )
    _install_node_instances(
        ctx,
        subgraph_node_instances,
        intact_nodes,
        NodeInstallationTasksSequenceCreator(),
        RuntimeInstallationTasksGraphFinisher,
        None
    )

#
# Create payload for completion status in ElasticSearch
#
def _create_payload(deployment_id,task,instance,step,logtype):
  #key='{}_{}'.format(deployment_id,task.id)
  item={
    'status': logtype,
    'deployment_id': deployment_id,  
    'node_id': instance.node_id,
    'instance_id':instance.id,
    'step': step,
    'task_id': task.id,
    'time': time.time()
  }
  return item

#
# Sets the on_failure handler in a task
#
def _add_es_log(ctx,instance,step,task):
  if( not ctx ):
    raise('null ctx object')
  if( not task):
    raise('null task supplied')

  #next line needed for proper capture by es_logger
  curfail=task.on_failure
  task.on_success=_create_handler(ctx,task,instance,step,'success')
  task.on_failure=_create_handler(ctx,task,instance,step,'fail')
  return task

def _create_handler(ctx,task,instance,step,cbtype):
  ctx.logger.info("create handler, cbtype={}, node={} instance={} step={}".format(cbtype,instance.node_id,instance.id,step))
  if( not ctx ):
    raise('null ctx object')
  if( not cbtype in ['fail','success']):
    raise('illegal cbtype={}'.format(cbtype))
  if( not task):
    raise('null task supplied')

  curcb=None
  if(cbtype == 'fail'):
    curcb=task.on_failure
  elif(cbtype == 'success'):
    curcb=task.on_success

  def es_logger(curtask=None):
    es=ES(ctx)
    pld=_create_payload(ctx.deployment.id,task,instance,step,cbtype)
    ctx.logger.info("posting {}:{}".format(cbtype,pld))
    resp=es.post(ctx.deployment.id,pld)
    ctx.logger.info("response={}".format(resp))
    if(curcb):
      return curcb(curtask)
    if(cbtype=='fail'):
      return workflow_tasks.HandlerResult.fail()
    if(cbtype=='success'):
      return workflow_tasks.HandlerResult.cont()
    return workflow_tasks.HandlerResult.fail()   # fail by default
 
  return es_logger
    

#
# Delete history for current deployment
#
def _clear_install_history(ctx):
  return ES(ctx).delete(ctx.deployment.id)

#
# Represents an ElasticSearch connection.  Only operates on the
# install index
#
class ES(object):

  def __init__(self,ctx):
    self._esurl=''
    ESPORT=9200
    mgr_ip='127.0.0.1'
    try:
      mgr_ip=utils.get_manager_ip()
    except:
      pass

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
  def __init__(self,ctx):
    self._did=ctx.deployment.id
    self._es=ES(ctx)
    self._get_history()
    self._history=self._get_history()

  def _get_history(self):
    hist=self._es.get("{}/_search?size=1000000".format(self._did)).json()
    self._history=[]
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
