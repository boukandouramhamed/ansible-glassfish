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
module: jboss
version_added: "1.4"
short_description: deploy applications to JBoss
description:
  - Deploy applications to JBoss standalone using the filesystem
options:
  deployment:
    required: true
    description:
      - The name of the deployment
  src:
    required: false
    description:
      - The remote path of the application ear or war to deploy
  deploy_path:
    required: false
    default: /var/lib/jbossas/standalone/deployments
    description:
      - The location in the filesystem where the deployment scanner listens
  state:
    required: false
    choices: [ present, absent ]
    default: "present"
    description:
      - Whether the application should be deployed or undeployed
notes:
  - "The JBoss standalone deployment-scanner has to be enabled in standalone.xml"
  - "Ensure no identically named application is deployed through the JBoss CLI"
author: "Jeroen Hoekx (@jhoekx)"
"""

EXAMPLES = """
# Deploy a hello world application
- jboss:
    src: /tmp/hello-1.0-SNAPSHOT.war
    deployment: hello.war
    state: present

# Update the hello world application
- jboss:
    src: /tmp/hello-1.1-SNAPSHOT.war
    deployment: hello.war
    state: present

# Undeploy the hello world application
- jboss:
    deployment: hello.war
    state: absent

# Update the hello world application
- glassfish:
    home: /opt/glassfish3/glassfish/bin
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

def is_runing(asadmin, domain):
    is_runing_ret = check_output(asadmin + " list-domains" , shell=True)

    if domain + " not" in is_runing_ret:
        return False
    else:
        return True

def start(asadmin, domain):
    is_start_ret = check_output("nohup " + asadmin + " start-domain " + domain , shell=True)

def stop(asadmin, domain):
    is_stop_ret = check_output(asadmin + " stop-domain " + domain , shell=True)

def delete_cache(home, domain):
    #path = os.path.join(home, "domains/" + domain + "/applications/")
    row = ['applications', 'osgi-cache','generated']
    for folder in row:
        path = os.path.join(home, "domains/" + domain + "/" + folder + "/")
        for soufolder in os.listdir(path):
            shutil.rmtree(os.path.join(path, soufolder))

def is_deleted(home, domain):
    row = ['applications', 'osgi-cache','generated']
    for folder in row:
        path = os.path.join(home, "domains/" + domain + "/" + folder + "/")
        for soufolder in os.listdir(path):
            if os.path.exists(soufolder):
                return False
    return True




def main():
    module = AnsibleModule(
        argument_spec=dict(
            home=dict(type='path', default='/APP/glassfish3/glassfish'),
            domain=dict(required=True),
            state=dict(choices=['stopped', 'started', 'restarted'], default='started'),
            del_cache=dict(choices=['yes', 'no'], default='no'),
        ),
        required_if=[('state', 'started', ('domain',))] # to be seen
    )

    result = dict(changed=False)
    
    home = module.params['home']
    domain = module.params['domain']
    state = module.params['state']
    del_cache = module.params['del_cache']
   
    if not os.path.exists(os.path.join(home, 'bin/asadmin')): 
        module.fail_json(msg="asadmin path does not exist.")

    else: asadmin = os.path.join(home, 'bin/asadmin')

    runing = is_runing(asadmin, domain)
    deleted = is_deleted(home, domain)

    if state == 'started' and not runing and del_cache == 'no':
        
        while not runing:
            start(asadmin, domain)
            runing = is_runing(asadmin, domain)
            time.sleep(1)

        result['changed'] = True

    if state == 'restarted' and del_cache == 'no':
        stop(asadmin, domain)
        runing = is_runing(asadmin, domain)
        while runing:
            stop(asadmin, domain)
            runing = is_runing(asadmin, domain)
            time.sleep(1)
        while not runing:
            start(asadmin, domain)
            runing = is_runing(asadmin, domain)
            time.sleep(1)
        result['changed'] = True

    if state == 'stopped' and runing and del_cache == 'no':
        while runing:
            stop(asadmin, domain)
            runing = is_runing(asadmin, domain)
            time.sleep(1)

        result['changed'] = True

#----------------------- handling cache ------------------------#
    if state == 'stopped' and del_cache == 'yes':
        while runing:
            stop(asadmin, domain)
            runing = is_runing(asadmin, domain)
            time.sleep(1)
        while not deleted:
            delete_cache(home, domain)
            deleted = is_deleted(home, domain)
        result['changed'] = True

    if state == 'started' and del_cache == 'yes':
        while runing:
            stop(asadmin, domain)
            runing = is_runing(asadmin, domain)
            time.sleep(1)
        while not deleted:
            delete_cache(home, domain)
            deleted = is_deleted(home, domain)               
        while not runing:
            start(asadmin, domain)
            runing = is_runing(asadmin, domain)
            time.sleep(1)            
        result['changed'] = True


    if state == 'restarted' and del_cache == 'yes':
        stop(asadmin, domain)
        runing = is_runing(asadmin, domain)
        while runing:
            stop(asadmin, domain)
            runing = is_runing(asadmin, domain)
            time.sleep(1)
        while not deleted:
            delete_cache(home, domain)
            deleted = is_deleted(home, domain)
        while not runing:
            start(asadmin, domain)
            runing = is_runing(asadmin, domain)
            time.sleep(1)
        result['changed'] = True

    module.exit_json(**result)

if __name__ == '__main__':
    main()
