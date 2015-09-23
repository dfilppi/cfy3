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

Represents a "microservice" in a Kubernetes cluster.  Requires the [`cloudify.kubernetes.relationships.connected_to_master`](#conn-to-master) relationship to get connection information.  Can define a service by plugin properties, by embedded Kubernetes native YAML, and by referring to a standard Kubernetes YAML deployment manifest while permitting overrides.  Actual command execution on Kubernetes is performed by the [fabric plugin](https://github.com/cloudify-cosmo/cloudify-fabric-plugin) by remotely executing the Kubernetes `kubectl` executable on the master node.

<b>Interesting properties</b>
TBD

#### cloudify.kubernetes.relationships.connected_to_master relationship <a id="#conn-to-master"></a>

Just retrieves the master ip and port for use by the dependent node.

#### Workflows
TBD

