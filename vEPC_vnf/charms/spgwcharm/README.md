# vnfproxy

A [Juju](https://jujucharms.com/) charm layer. See [how it works](https://jujucharms.com/how-it-works) and the [Getting Started](https://jujucharms.com/docs/stable/developer-getting-started) page for more information about Juju and Charms.

[OSM](https://osm.etsi.org/) is an [ETSI](http://www.etsi.org/)-hosted project to develop an Open Source NFV Management and Orchestration (MANO) software stack aligned with ETSI NFV.

## Overview

The vnfproxy [layer](https://jujucharms.com/docs/stable/developer-layers) is intended for use by vendors who wish to integrate a VNF with OSM. The current release of OSM only supports a lightweight version of Juju charms, which we refer to as VNF Configuration or "proxy" charms.

This document will describe the steps necessary to create a charm for your VNF.

First, consider the diagram below:

```
+---------------------+    +---------------------+
|                     <----+                     |
|  Resource           |    |  Service            |
|  Orchestrator (RO)  +---->  Orchestrator (SO)  |
|                     |    |                     |
+------------------+--+    +-------+----^--------+
                   |               |    |
                   |               |    |
                   |               |    |
             +-----v-----+       +-v----+--+
             |           <-------+         |
             |  Virtual  |       |  Proxy  |
             |  Machine  |       |  Charm  |
             |           +------->         |
             +-----------+       +---------+
```

The Virtual Machine (VM) is created by the Resource Orchestrator (RO), at the
request of the Service Orchestrator (SO). Once the VM has been created, a
"proxy charm" is deployed in order to facilitate operations between the SO and
your service running within the VM.

As such, a proxy charm will expose a number of actions -- also known as service primitives -- that are run by the SO. By default, the following actions are exposed:

```bash
actions
├── reboot
├── restart
├── run
├── start
├── stop
└── upgrade
```

Some actions, such as `run` and `reboot`, do not require any additional configuration. The rest, however, require you to implement the command(s) required to interact with your VNF.

A charm is composed of multiple layers of code. The layer you create for your VNF is the topmost layer. It will include the basic layer, which provides the framework for building reactive charms, and the vnfproxy layer, which adds functionality specific to operating and configuring VNFs. Finally, these layers are combined to form the charm you'll place inside your VNF Descriptor Package.

## Step 1: Create the layer for your proxy charm:

Create a new charm layer, substituting "myvnf" with the name of your VNF.

```bash
$ charm create myvnf
$ cd myvnf
```

Modify `layer.yaml` to the following:
```yaml
includes:
    - layer:basic
    - layer:vnfproxy
```

The `metadata.yaml` describes your service. It should look similar to the following:

```yaml
name: myvnf
summary: My VNF provides a specific virtualized network function.
maintainer: Adam Israel <adam.israel@canonical.com>
description: |
  A longer description of your VNF and what it provides to users.
series:
  - xenial
tags:
  - osm
  - vnf
subordinate: false
```

### Actions (Service Primitives)

In Juju, Service Primitives are referred to as Actions. These are commands that will be executed on the VNF on request of the Service Orchestrator.

#### Defining Actions

Actions are defined through a yaml file called `actions.yaml` in the root directory of your charm. This file describes the action and the parameters it requires in order to execute.

```yaml
configure-server:
    description: "Configure a thing"
    params:
      polling-interval:
        type: int
        description: "The interval, in seconds, to poll a thing."
        default: 30

```
#### Implementing your Actions

We use executable files in the charm's `actions/` directory to invoke a reactive handler for your VNF logic. Each file should have the same name as the action you defined in `actions.yaml`.

Cut and paste the following into `actions/configure-server` and `chmod +x actions/configure-server`:

```bash
#!/usr/bin/env python3
import sys
sys.path.append('lib')

from charms.reactive import main
from charms.reactive import set_state
from charmhelpers.core.hookenv import action_fail, action_name

"""
`set_state` only works here because it's flushed to disk inside the `main()`
loop. remove_state will need to be called inside the action method.
"""
set_state('actions.{}'.format(action_name()))

try:
    main()
except Exception as e:
    action_fail(repr(e))
```

Next, we'll add the code that will be executed inside your VNF via the ssh credentials. Open `reactive/myvnf.py` and add the following reactive handler code:

```python
# Change configure-server to match the name of the action you want to execute.
@when('actions.configure-server')
def configure_server():
    err = ''
    try:
        # Put the code here that you want to execute
        cmd = ""
        result, err = charms.sshproxy._run(cmd)
    except:
        action_fail('command failed:' + err)
    else:
        action_set({'output': result})
    finally:
        remove_flag('actions.start')

```

#### Default Actions (Service Primitives)

The vnfproxy layer defines several default actions that you may implement. If you choose not to implement these, the actions will do nothing.

Add the following code to `reactive/myvnf.py` and fill in the `cmd` variable with the command to be run on your VNF:

```python
@when('actions.start')
def start():
    err = ''
    try:
        # Put the code here that you want to execute
        cmd = ""
        result, err = charms.sshproxy._run(cmd)
    except:
        action_fail('command failed:' + err)
    else:
        action_set({'output': result})
    finally:
        remove_flag('actions.start')


@when('actions.stop')
def stop():
    err = ''
    try:
        # Enter the command to stop your service(s)
        cmd = "service myname stop"
        result, err = charms.sshproxy._run(cmd)
    except:
        action_fail('command failed:' + err)
    else:
        action_set({'output': result})
    finally:
        remove_flag('actions.stop')


@when('actions.restart')
def restart():
    err = ''
    try:
        # Enter the command to restart your service(s)
        cmd = "service myname restart"
        result, err = charms.sshproxy._run(cmd)
    except:
        action_fail('command failed:' + err)
    else:
        action_set({'output': result})
    finally:
        remove_flag('actions.restart')

  @when('actions.upgrade')
  def upgrade_vnf():
    """Upgrade the software on the VNF.

    This action is intended to be used to perform software upgrades on a running VNF.
    """
      err = ''
      try:
          # Enter the command (s) to upgrade your VNF software
          cmd = ""
          result, err = charms.sshproxy._run(cmd)
      except:
          action_fail('command failed:' + err)
      else:
          action_set({'output': result})
      finally:
          remove_flag('actions.upgrade')        
```

Rename `README.ex` to `README.md` and describe your application and its usage.

### Configuration

Charms support immutable configuration, defined by the `config.yaml` file. In the case of OSM, it's configuration is primarily driven through service primitives. Feel free to delete `config.yaml`.

### Metrics

Juju supports the polling of metrics. To do this, create the `metrics.yaml` file in the root directory of your charm, following the example below. The command specified will be executed inside your VNF; it should return a positive decimal number. The collected metrics will be made available to OSM, beginning with Release 4.

```yaml
metrics:
    uptime:
        type: gauge
        description: "Seconds since the machine was rebooted."
        command: awk '{print $1}' /proc/uptime

```

These metrics are collected automatically by way of the `collect-metrics` hook, are stored in the Juju Controller, and will be periodically polled by the OSM MON module.

### Building your VNF charm

Once you've implemented your actions, you need to compile the various charm layers. From the charm's root directory:
```bash
$ charm build
```

This will combine all of the layers required by your VNF layer into a single charm, in the builds/ directory. At this point, the charm can be delivered to a Network Operator for onboarding.

### VNF Descriptor Package
Copy the combined charm into the `charm` directory of your [VNF package]:

```
├── charm
│   └── myvnf
├── cloud_init
│   └── myvnf_cloud_init.cfg
├── icons
│   └── myvnf_logo.png
└── myvnf_vnfd.yaml
```

## Contact

Send an email to the OSM_TECH@list.etsi.org mailing list.

[VNF package]: https://osm.etsi.org/wikipub/index.php/Creating_your_own_VNF_package_(Release_TWO)
