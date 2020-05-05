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

@when_not('spgwcharm.installed')
def install_spgwcharm():
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
    set_flag('spgwcharm.installed')


@when('actions.configure-spgw')
def configure_spgw():
    hss_ip = action_get('hss-ip')
    spgw_ip = action_get('spgw-ip')
    cmd1 = "sudo ip link set ens4 up && sudo dhclient ens4"
    charms.sshproxy._run(cmd1)
    cmd2 = "sudo ip link set ens5 up && sudo dhclient ens5"
    charms.sshproxy._run(cmd2)
    cmd3 = "sudo ip link set ens6 up && sudo dhclient ens6"
    charms.sshproxy._run(cmd3)
    cmd3='sudo sed -i "\'s/$hss_ip/{}/g\'" /etc/nextepc/freeDiameter/mme.conf'.format(hss_ip)
    charms.sshproxy._run(cmd3)
    cmd4='sudo sed -i "\'s/$spgw_ip/{}/g\'" /etc/nextepc/freeDiameter/mme.conf'.format(spgw_ip)
    charms.sshproxy._run(cmd4)    
    remove_flag('actions.configure-spgw')

@when('actions.restart-spgw')
def restart_spgw():
    cmd = "sudo systemctl restart nextepc-mmed"
    charms.sshproxy._run(cmd)
    remove_flag('actions.restart-spgw')

@when('actions.add-route')
def add_route():
    prefix = action_get('external-prefix')
    next_hop = action_get('next-hop')
    cmd = "sudo route add -net " + prefix + " gw " + next_hop
    charms.sshproxy._run(cmd)
    remove_flag('actions.add-route')