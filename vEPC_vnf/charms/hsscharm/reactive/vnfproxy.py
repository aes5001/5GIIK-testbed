from charmhelpers.core.hookenv import (
    action_fail,
    action_set,
)

from charms.reactive import (
    when,
    clear_flag,
)
import charms.sshproxy


@when('actions.reboot')
def reboot():
    err = ''
    try:
        result, err = charms.sshproxy._run("reboot")
    except:
        action_fail('command failed:' + err)
    else:
        action_set({'outout': result})
    finally:
        clear_flag('actions.reboot')


###############################################################################
# Below is an example implementation of the start/stop/restart actions.       #
# To use this, copy the below code into your layer and add the appropriate    #
# command(s) necessary to perform the action.                                 #
###############################################################################

# @when('actions.start')
# def start():
#     err = ''
#     try:
#         cmd = "service myname start"
#         result, err = charms.sshproxy._run(cmd)
#     except:
#         action_fail('command failed:' + err)
#     else:
#         action_set({'outout': result})
#     finally:
#         clear_flag('actions.start')
#
#
# @when('actions.stop')
# def stop():
#     err = ''
#     try:
#         # Enter the command to stop your service(s)
#         cmd = "service myname stop"
#         result, err = charms.sshproxy._run(cmd)
#     except:
#         action_fail('command failed:' + err)
#     else:
#         action_set({'outout': result})
#     finally:
#         clear_flag('actions.stop')
#
#
# @when('actions.restart')
# def restart():
#     err = ''
#     try:
#         # Enter the command to restart your service(s)
#         cmd = "service myname restart"
#         result, err = charms.sshproxy._run(cmd)
#     except:
#         action_fail('command failed:' + err)
#     else:
#         action_set({'outout': result})
#     finally:
#         clear_flag('actions.restart')
#
#
# @when('actions.upgrade')
# def upgrade_vnf():
#     err = ''
#     try:
#         # Add the command(s) to perform a VNF software upgrade
#         cmd = ''
#         result, err = charms.sshproxy._run(cmd)
#     except:
#         action_fail('command failed:' + err)
#     else:
#         action_set({'outout': result})
#     finally:
#         clear_flag('actions.upgrade')
#
