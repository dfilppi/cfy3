## Cloudify Kubernetes Plugin

This project contains a plugin that enables Cloudify to install, configure, and run services on a Kubernetes cluster.  The current plugin has only been testing cfy local mode, and uses the [fabric plugin](https://github.com/cloudify-cosmo/cloudify-fabric-plugin) to perform the installation and configuration of Kubernetes.

Limitations (as of 9/23/15):
+ Only tested on Ubuntu 14
+ Only tested in local mode

### Plugin components

#### cloudify.kubernetes.Master node type

Represents a Kuberenets master node.  This is the only essential node in the plugin.  All other node types and workflows require a master node to be defined.  By default, it will install Kubernetes to the identified host, but it can be configured to merely connect to an existing master.  If desired, the blueprint will also install docker if the `install_docker` property is `true`.

<b>Interesting properties</b>
+ install_agent      boolean (default=false) that determines whether to install a Cloudify agent on the target host.
+ install_docker     boolean (default=false) that determines whether the plugin will install docker before attempting to install Kuberenets
+ install            boolean (default=true) that determines whether the plugin will install Kubernetes itself.  If `false`, it will simply connect
+ master_port        int (default 8080) that indicates where Kubernetes will listen for requests 

#### cloudify.kubernetes.Node node type

Represents a Kubernetes "node" or "minion".  Unused if simply connecting to an existing cluster.  Extracts connection information to the master via the [`cloudify.kubernetes.relationships.connected_to_master`](#conn-to-master) relationship.

#### cloudify.kubernetes.MicroService type

Represents a "microservice" in a Kubernetes cluster.  Requires the [`cloudify.kubernetes.relationships.connected_to_master`](#conn-to-master) relationship to get connection information.  Can define a service by plugin properties, by embedded Kubernetes native YAML, and by referring to a standard Kubernetes YAML deployment manifest while permitting overrides.  When using either form of native YAML, the actual Kubernetes action performed is determined by the configuration, which means that in reality it may or may not actually create a Kubernetes service, replication control, or other artifact.  Actual command execution on Kubernetes is performed by the [fabric plugin](https://github.com/cloudify-cosmo/cloudify-fabric-plugin) by remotely executing the Kubernetes `kubectl` executable on the master node.

<b>Interesting properties</b>
<li> non-native service definition - uses kubectl on master to first run a "run" command, followed by an "expose" command.

 Property        | Description                                   
 --------------- |  ---------------------
 name            | service name                                  
 image           | image name                                    
 port            | service listening port                        
 target_port     | container port (default:port)                 
 protocol        | TCP/UDP  (default TCP)                        
 replicas        | number of replicas (default 1)                   
 run_overrides   | json overrides for kubectl "run"              
 expose_overrides| json overrides for kubectl "expose"          

<nbsp>
<li>native embedded properties

 Property        | Description                                 
 --------------- | ---------------------------------------------
 config          | indented children are native Kubernetes YAML

<nbsp>
<li>native file reference properties

 Property        | Description                                
 --------------- | ---------------------------------------------
 config_path     | path to Kubernetes manifest               
 config_overrides| replacement values for external manifest 


#### cloudify.kubernetes.relationships.connected_to_master relationship <a id="#conn-to-master"></a>

Just retrieves the master ip and port for use by the dependent node.

#### Workflows

These workflows just delegate to `kubectl` on the master.  They all share a parameter called `master`.  The `master` parameter is set to the node name of the Kubernetes master that the workflow is to be run against.  Another pattern is to provide many (but not all) of the parameters that `kubectl` accepts, but using the `overrides` property as a catch all.
These workflows are provided as samples.  It should be understood that any actual producion blueprint would only implement workflows relevant to the blueprint purpose, which may or may not include the following, and probably contain others.

Workflow name| Description
------ | -------
kube_run         | `kubectl run` equivalent
kube_expose      | `kubectl run` equivalent
kube_stop        | `kubectl stop` equivalent
kube_delete      | `kubectl delete` equivalent
