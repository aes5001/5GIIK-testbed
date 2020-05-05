"""Module to help with executing commands over SSH."""
##
# Copyright 2016 Canonical Ltd.
# All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.
##

from charmhelpers.core import unitdata
from charmhelpers.core.hookenv import log

import io
import ipaddress
import paramiko
import os
import socket
import shlex
import traceback

from subprocess import (
    Popen,
    CalledProcessError,
    PIPE,
)


def get_config():
    """Get the current charm configuration.

    Get the "live" kv store every time we need to access the charm config, in
    case it has recently been changed by a config-changed event.
    """
    db = unitdata.kv()
    return db.get('config')


def get_host_ip():
    """Get the IP address for the ssh host.

    HACK: This function was added to work around an issue where the
    ssh-hostname was passed in the format of a.b.c.d;a.b.c.d, where the first
    is the floating ip, and the second the non-floating ip, for an Openstack
    instance.
    """
    cfg = get_config()
    return cfg['ssh-hostname'].split(';')[0]


def is_valid_hostname(hostname):
    """Validate the ssh-hostname."""
    log("Hostname: {}".format(hostname))
    if hostname == "0.0.0.0":
        return False

    try:
        ipaddress.ip_address(hostname)
    except ValueError:
        return False

    return True


def verify_ssh_credentials():
    """Verify the ssh credentials have been installed to the VNF.

    Attempts to run a stock command - `hostname` on the remote host.
    """
    verified = False
    status = ''
    cfg = get_config()

    try:
        host = get_host_ip()
        if is_valid_hostname(host):
            if len(cfg['ssh-hostname']) and len(cfg['ssh-username']):
                cmd = 'hostname'
                status, err = _run(cmd)

                if len(err) == 0:
                    verified = True
        else:
            status = "Invalid IP address."
    except CalledProcessError as e:
        status = 'Command failed: {} ({})'.format(
            ' '.join(e.cmd),
            str(e.output)
        )
    except paramiko.ssh_exception.AuthenticationException as e:
        status = '{}.'.format(e)
    except paramiko.ssh_exception.BadAuthenticationType as e:
        status = '{}'.format(e.explanation)
    except paramiko.ssh_exception.BadHostKeyException as e:
        status = 'Host key mismatch: expected {} but got {}.'.format(
            e.expected_key,
            e.got_key,
        )
    except (TimeoutError, socket.timeout):
        status = "Timeout attempting to reach {}".format(cfg['ssh-hostname'])
    except Exception as error:
        tb = traceback.format_exc()
        status = 'Unhandled exception: {}'.format(tb)

    return (verified, status)


def charm_dir():
    """Return the root directory of the current charm."""
    d = os.environ.get('JUJU_CHARM_DIR')
    if d is not None:
        return d
    return os.environ.get('CHARM_DIR')


def run_local(cmd, env=None):
    """Run a command locally."""
    if isinstance(cmd, str):
        cmd = shlex.split(cmd) if ' ' in cmd else [cmd]

    if type(cmd) is not list:
        cmd = [cmd]

    p = Popen(cmd,
              env=env,
              shell=True,
              stdout=PIPE,
              stderr=PIPE)
    stdout, stderr = p.communicate()
    retcode = p.poll()
    if retcode > 0:
        raise CalledProcessError(returncode=retcode,
                                 cmd=cmd,
                                 output=stderr.decode("utf-8").strip())
    return (stdout.decode('utf-8').strip(), stderr.decode('utf-8').strip())


def _run(cmd, env=None):
    """Run a command remotely via SSH.

    Note: The previous behavior was to run the command locally if SSH wasn't
    configured, but that can lead to cases where execution succeeds when you'd
    expect it not to.
    """
    if isinstance(cmd, str):
        cmd = shlex.split(cmd)

    if type(cmd) is not list:
        cmd = [cmd]

    cfg = get_config()

    if cfg:
        if all(k in cfg for k in ['ssh-hostname', 'ssh-username',
                                  'ssh-password', 'ssh-private-key']):
            host = get_host_ip()
            user = cfg['ssh-username']
            passwd = cfg['ssh-password']
            key = cfg['ssh-private-key']  # DEPRECATED

            if host and user:
                return ssh(cmd, host, user, passwd, key)

    raise Exception("Invalid SSH credentials.")


def get_ssh_client(host, user, password=None, key=None):
    """Return a connected Paramiko ssh object."""
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    pkey = None

    # Check for the DEPRECATED private-key
    if key:
        f = io.StringIO(key)
        pkey = paramiko.RSAKey.from_private_key(f)
    else:
        # Otherwise, check for the auto-generated private key
        if os.path.exists('/root/.ssh/id_juju_sshproxy'):
            with open('/root/.ssh/id_juju_sshproxy', 'r') as f:
                pkey = paramiko.RSAKey.from_private_key(f)

    ###########################################################################
    # There is a bug in some versions of OpenSSH 4.3 (CentOS/RHEL 5) where    #
    # the server may not send the SSH_MSG_USERAUTH_BANNER message except when #
    # responding to an auth_none request. For example, paramiko will attempt  #
    # to use password authentication when a password is set, but the server   #
    # could deny that, instead requesting keyboard-interactive. The hack to   #
    # workaround this is to attempt a reconnect, which will receive the right #
    # banner, and authentication can proceed. See the following for more info #
    # https://github.com/paramiko/paramiko/issues/432                         #
    # https://github.com/paramiko/paramiko/pull/438                           #
    ###########################################################################

    try:
        client.connect(host, port=22, username=user,
                       password=password, pkey=pkey)
    except paramiko.ssh_exception.SSHException as e:
        if 'Error reading SSH protocol banner' == str(e):
            # Once more, with feeling
            client.connect(host, port=22, username=user,
                           password=password, pkey=pkey)
        else:
            # Reraise the original exception
            raise e

    return client


def sftp(local_file, remote_file, host, user, password=None, key=None):
    """Copy a local file to a remote host."""
    client = get_ssh_client(host, user, password, key)

    # Create an sftp connection from the underlying transport
    sftp = paramiko.SFTPClient.from_transport(client.get_transport())
    sftp.put(local_file, remote_file)
    client.close()


def ssh(cmd, host, user, password=None, key=None):
    """Run an arbitrary command over SSH."""
    client = get_ssh_client(host, user, password, key)

    cmds = ' '.join(cmd)
    stdin, stdout, stderr = client.exec_command(cmds, get_pty=True)
    retcode = stdout.channel.recv_exit_status()
    client.close()  # @TODO re-use connections
    if retcode > 0:
        output = stderr.read().strip()
        raise CalledProcessError(returncode=retcode, cmd=cmd,
                                 output=output)
    return (
        stdout.read().decode('utf-8').strip(),
        stderr.read().decode('utf-8').strip()
    )
