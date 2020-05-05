from charms.reactive import when, when_not, set_flag

from charmhelpers.core.hookenv import (
    action_get,
    action_fail,
    action_set,
    config,
    status_set,
)

from charms.reactive import (
    remove_state as remove_flag,
    set_state as set_flag,
    when, when_not
)

import charms.sshproxy

@when_not('hsscharm.installed')
def install_hsscharm():
    # Do your setup here.
    #
    # If your charm has other dependencies before it can install,
    # add those as @when() clauses above., or as additional @when()
    # decorated handlers below
    #
    # See the following for information about reactive charms:
    #
    #  * https://jujucharms.com/docs/devel/developer-getting-started
    #  * https://github.com/juju-solutions/layer-basic#overview
    #
    set_flag('hsscharm.installed')


@when('actions.configure-hss')
def configure_hss():
    spgw_ip = action_get('spgw-ip')
    hss_ip = action_get('hss-ip')
    cmd1 = "sudo ip link set ens4 up && sudo dhclient ens4"
    charms.sshproxy._run(cmd1)
    cmd2= 'sudo sed -i "\'s/$hss_ip/{}/g\'" /etc/nextepc/freeDiameter/hss.conf'.format(hss_ip)
    charms.sshproxy._run(cmd2)
    cmd3= 'sudo sed -i "\'s/$spgw_ip/{}/g\'" /etc/nextepc/freeDiameter/hss.conf'.format(spgw_ip)
    charms.sshproxy._run(cmd3)
    remove_flag('actions.configure-hss')

@when('actions.restart-hss')
def restart_hss():
    cmd = "sudo systemctl restart nextepc-hssd"
    charms.sshproxy._run(cmd)
    remove_flag('actions.restart-hss') 
