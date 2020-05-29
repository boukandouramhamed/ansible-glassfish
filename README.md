# Ansible module to manage glassfish domain.
A simple module to manage your glassfish server and to also deploy your applications.

### Installation: 
You need only to add the modules to your main modules folder.

### Examples: 
- glassfish:     
    asadir: "Path to bin"     
    src: "path to application"     
    deployment: "deployment name"
    server: "target server"
    port: "port"
    state: present
