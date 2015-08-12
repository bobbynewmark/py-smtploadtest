from azure import *
from azure.servicemanagement import *
import sys, time, hashlib
from fabric.api import *
import fabric.network
import os
import json
import StringIO

def make_vmname():
    hash = hashlib.sha1()
    hash.update(str(time.time()))
    rand = hash.hexdigest()
    return hash.hexdigest()[:10]

def template_config(path, replacements):
    with open(path) as f:
        obj = json.load(f)
        for key in replacements.keys():
            obj[key] = replacements[key]
        retval = StringIO.StringIO(json.dumps(obj))
        retval.name = "config.json"
        return retval

def make_machine(sms, location, name, create_cloudapp, image_name, user, password, storage_account, extra_endpoints ):
    if (create_cloudapp):
        sms.create_hosted_service(service_name=name,
            label=name,
            location=location)

    hosted_service_name = name #'catcher-bp'
    public_dns = hosted_service_name + ".cloudapp.net"
    hostname = name

    container = name # "os-image"
    blob = name + "-linux.os.vhd"
    windows_blob_url = "blob.core.windows.net"
    media_link = "http://" + storage_account + "." + windows_blob_url + "/" + container + "/" + blob

    linux_config = LinuxConfigurationSet(hostname,user,password, False)
    os_hd = OSVirtualHardDisk(image_name, media_link)

    network = ConfigurationSet()
    network.configuration_set_type = 'NetworkConfiguration'
    network.input_endpoints.input_endpoints.append(ConfigurationSetInputEndpoint('ssh', 'tcp', '22', '22'))
    for item in extra_endpoints:
        network.input_endpoints.input_endpoints.append(ConfigurationSetInputEndpoint(*item))

    result = sms.create_virtual_machine_deployment(service_name=hosted_service_name,
        deployment_name=name,
        deployment_slot='production',
        label=name,
        role_name=name,
        system_config=linux_config,
        os_virtual_hard_disk=os_hd,
        network_config=network,
        role_size='Small')

    for i in range(10):
        operation_result = sms.get_operation_status(result.request_id)
        print('Operation status: ' + operation_result.status)
        if (operation_result.status == 'Succeeded'):
            break
        time.sleep(30)

    for i in range(10):
        props = sms.get_deployment_by_name(hosted_service_name, name)
        print hosted_service_name, name, props.status, props.role_instance_list[0].instance_status
        if props.role_instance_list[0].instance_status == 'ReadyRole':
            break
        time.sleep(30)
    return public_dns

def create_sink(public_dns):
    env.hosts = [ public_dns ]
    env.host_string = public_dns
    env.user = user
    env.password = password
    env.disable_known_hosts = True

    sudo("apt-get install git-core -y")
    sudo("apt-get install python-twisted -y")
    run("git clone https://github.com/bobbynewmark/py-smtploadtest.git")
    with cd("~/py-smtploadtest"):
        run("twistd -o -y sink.tac && sleep 5")
        run("tail twistd.pid")

def create_pitcher(public_dns, configjson, email_from_file, attachments):
    env.hosts = [ public_dns ]
    env.host_string = public_dns
    env.user = user
    env.password = password
    env.disable_known_hosts = True

    sudo("apt-get install git-core -y")
    sudo("apt-get install python-twisted -y")
    run("git clone https://github.com/bobbynewmark/py-smtploadtest.git")
    with cd("~/py-smtploadtest"):
        put(configjson, '~/py-smtploadtest/config.json')
        put(email_from_file, '~/py-smtploadtest')
        for att in attachments:
            put(att, '~/py-smtploadtest')
        run("twistd -o -y pitcher.tac && sleep 5")
        run("tail twistd.pid")

if __name__ == "__main__":
    sub_id = sys.argv[1]
    cert = sys.argv[2]
    sms = ServiceManagementService(sub_id,cert)
    location = sys.argv[3]
    user = sys.argv[4]
    password = sys.argv[5]
    #an Ubuntu-14_10 image 
    image_name = 'b39f27a8b8c64d52b05eac6a62ebad85__Ubuntu-14_10-amd64-server-20141022.3-en-us-30GB'
    storage_account = sys.argv[6]
    rebuildSink = False

    sinkDNS = 'sink-bp.cloudapp.net'
    if rebuildSink:
        extra_endpoints = [('email', 'tcp', '25', '8001'),('web', 'tcp', '80', '8002')]
        sinkDNS = make_machine(sms, location, 'sink-bp', True, image_name, user, password, storage_account, extra_endpoints)
        create_sink(sinkDNS)


    configjson = template_config('config-template.json', {'scoreboard_url': 'http://'+sinkDNS , 'smtp_ip':sinkDNS, 'smtp_port':25})
    email_from_file = 'emailtos.txt'
    attachments = ['marker.gif', 'big.jpg']

    pitcherDNS = make_machine(sms, location, make_vmname(), True, image_name, user, password, storage_account, [])
    create_pitcher(pitcherDNS, configjson, email_from_file, attachments)
    print "SINK AT ", sinkDNS
    print "CREATED PITCHER AT ", pitcherDNS
