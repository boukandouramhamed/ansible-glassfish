#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2013, Jeroen Hoekx <jeroen.hoekx@dsquare.be>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = """
# Update the hello world application
- glassfish:
    asadir: /opt/glassfish3/glassfish/bin
    src: /tmp/hello-1.1-SNAPSHOT.war
    deployment: hello
    server: server
    port: 4848
    state: present
"""

import os
import shutil
import time
from ansible.module_utils.basic import AnsibleModule
from subprocess import check_output

def is_enabled(deployment, asadmin):
    is_enabled_ret = check_output(asadmin + " get servers.server.server.application-ref." + deployment + ".enabled", shell=True)

    if 'true' in is_enabled_ret:
        return True
    else:
        return False

def enabling(deployment, asadmin):
    is_enabled_ret = check_output(asadmin + " set servers.server.server.application-ref." + deployment + ".enabled=true", shell=True)


def disable(deployment, asadmin):
    is_enabled_ret = check_output(asadmin + " set servers.server.server.application-ref." + deployment + ".enabled=false", shell=True)


def is_deployed(deployment, asadmin):
    is_deployed_ret = check_output( asadmin + "  list-applications", shell=True)

    if deployment in is_deployed_ret:
        return True
    else:
        return False

def deploy(deployment, server, port, asadmin, path):
    # deployment path 
    deploy_ret = check_output( asadmin + " -p " + port + " deploy --verify=true --precompilejsp=true --name " + deployment + " --enabled=true --virtualservers " + server + " " + path , shell=True)

def undeploy(deployment, port, asadmin):
    deploy_ret = check_output(asadmin + " -p " + port + " undeploy " + deployment , shell=True)   
                                                    
def set_default_context(server, port, context):
    default_cntx = check_output( "asadmin -p " + port + " set configs.config.server-config.http-service.virtual-server." + server + ".default-web-module=" + context , shell=True)

def main():
    module = AnsibleModule(
        argument_spec=dict(
            asadir=dict(type='path', default='/APP/glassfish3/glassfish/bin'),
            src=dict(type='path'),
            path=dict(type='path',required=True),
            deployment=dict(required=True),
            server=dict(default='server'),
            port=dict(default='4848'),
            state=dict(choices=['absent', 'present'], default='present'),
            context=dict(default=''),
            enable=dict(choices=['yes', 'no'], default='yes'),
        ),
        required_if=[('state', 'present', ('src',))]
    )

    result = dict(changed=False)
    
    asadir = module.params['asadir']
    src = module.params['src']
    path = module.params['path']
    deployment = module.params['deployment']
    server = module.params['server']
    context = module.params['context']
    port = module.params['port']
    state = module.params['state']
    enable = module.params['enable']
   
    if not os.path.exists(os.path.join(asadir, 'asadmin')): 
        module.fail_json(msg="asadmin path does not exist.")
    else: asadmin = os.path.join(asadir, 'asadmin')

    #if not os.path.exists(os.path.join(path, deployment + '.ear')): 
    if not os.path.exists(path): 
        module.fail_json(msg="Path to ear does not exist")
    #else: path = os.path.join(path, deployment + '.ear')


    deployed = is_deployed(deployment, asadmin)

    if deployed:
        enabled = is_enabled(deployment, asadmin)

    if state == 'present' and not deployed and enable == 'yes':
       # if not os.path.exists(src): # add this to undeployed
        #    module.fail_json(msg='Source file %s does not exist.' % src)

        while not deployed:
            deploy(deployment, server, port, asadmin, path)
            deployed = is_deployed(deployment, asadmin)
            time.sleep(1)
        result['changed'] = True

    if state == 'present' and not deployed and enable == 'no':
        #if not os.path.exists(src): # add this to undeployed
            #module.fail_json(msg='Source file %s does not exist.' % src)

        while not deployed:
            deploy(deployment, server, port, asadmin, path)
            deployed = is_deployed(deployment, asadmin)
            time.sleep(1)
        enabled = is_enabled(deployment, asadmin)
        while enabled:
            disable(deployment, asadmin)
            enabled = is_enabled(deployment, asadmin)
            time.sleep(1)

        result['changed'] = True

    if deployed:
        enabled = is_enabled(deployment, asadmin)

    if state == 'present' and deployed and enable == 'yes' and enabled:      
        while deployed:
            undeploy(deployment, port, asadmin)
            deployed = is_deployed(deployment, asadmin)
        while not deployed:
            deploy_ret = deploy(deployment, server, port, asadmin, path)
            deployed = is_deployed(deployment, asadmin)
            time.sleep(1)
        result['changed'] = True

#------ To re-examin
    if state == 'present' and deployed and enable == 'yes' and not enabled:
        while not enabled:
            enabling(deployment, asadmin)
            enabled = is_enabled(deployment, asadmin)
        result['changed'] = True

    if state == 'present' and deployed and enable == 'no' and enabled:
        while enabled:
            disable(deployment, asadmin)
            enabled = is_enabled(deployment, asadmin)
        result['changed'] = True

    if state == 'absent' and deployed:
        while deployed:
            undeploy(deployment, port, asadmin)
            deployed =  is_deployed(deployment, asadmin)
            time.sleep(1)
        result['changed'] = True

    module.exit_json(**result)
#-------- default context
    if state == 'present' and deployed and enabled:
        set_default_context(server, port, context) #set default context
        
        result['changed'] = True

if __name__ == '__main__':
    main()
