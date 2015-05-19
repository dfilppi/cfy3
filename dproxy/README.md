## Deployment proxy plugin

The dproxy plugin connects two deployments in order to allow deployment coordination.  The source blueprint that wishes to depend on another blueprint (for example a web tier that wants to depend on a database), includes the cloudify.nodes.
DeploymentProxy node in the blueprint and creates a depends-on or other relation
ship with it.  The DeploymentProxy node waits for a condition to be satisfied by the outputs of the target blueprint.  The DeploymentProxy node itself has the following properties that govern it's behavior:

- deployment_id          : the deployment to depend on
- wait_for               : either "exists" or "expr".  If "exists", will wait for
                           an output matching the value of property "test".  If
                           "expr", it interprets property "test" as a python
                           boolean expression, in which the collection "outputs"
                           is the outputs dict (e.g. expr: outputs[port]>0
- test                   : either the name of an output, or a boolean expression
                           (see wait_for)
- timeout                : number of seconds to wait.  When timeout expires, a "RecoverableError" is thrown.  Default=30.


In the "example" directory, a sample openstack and single node blueprint for both MongoDb and Nodejs (adapted from the standard Nodecellar blueprint) demonstrate a simple dependency.  Note that the plugin is embedded in the plugins directory of the Nodejs blueprint.

