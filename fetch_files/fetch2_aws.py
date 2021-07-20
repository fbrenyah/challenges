#!/usr/bin/python3
# Purpose:      Fetch Rewards Coding Assessment - Site Reliability Engineer
#               Spin up an EC2 instance, using confs from a yaml file, in default AZ
#               with multiple volumes and SSH users that can connect to the instance
# Date:         July 20, 2021
# Written by:   Frank Brenyah
#
# Use: python3 fetch2_aws.py <yaml_file> <key_name>
# Ex: python3 fetch2_aws.py ec2conf.yml ec2-keypair
#
import sys
import time
import subprocess
import boto3
from botocore.exceptions import ClientError
import yaml

def force_quit():  # force a quit, the script has failed
    print("\tThis script cannot continue. Terminating!")
    sys.exit()
# end force_quit()

def find_ami():
    print("Searching for AMI to use...")
    global ec2
    client = ec2.meta.client
    image = client.describe_images(Filters=[{
                'Name': 'architecture',
                'Values': [arch_type],
                'Name': 'root-device-type',
                'Values': [root_dev],
                'Name': 'virtualization-type',
                'Values': [virt_type],
                'Name': 'state',
                'Values': ['available'],
                'Name': 'owner-alias',
                'Values': ['amazon'],
                'Name': 'description',
                'Values': ['Amazon Linux*']
            },
        ],
        IncludeDeprecated=False,
        DryRun=False
    )['Images'][0]['ImageId']
    print("\tChosen AMI:", image)
    return image  # return the AMI ID; is string
# end find_ami()

def get_goodies(confs, file):
    print("Getting confs from:", file)
    try:
        global max_count
        max_count = confs['server']['max_count']
        global min_count
        min_count = confs['server']['min_count']
        global inst_type
        inst_type = confs['server']['instance_type']
        global ami_type
        ami_type = confs['server']['ami_type']
        global arch_type
        arch_type = confs['server']['architecture']
        global root_dev
        root_dev = confs['server']['root_device_type']
        global virt_type
        virt_type = confs['server']['virtualization_type']
    except Exception as e:
        print("Failed to get configurations!", e)

    print("\tAMI Type:", ami_type)
    print("\tInstance Type:", inst_type)
    print("\tArchitecture Type:", arch_type)
    print("\tRoot Device Type:", root_dev)
# end get_goodies()

def get_ssh_keys(confs):
    print("Getting user SSH keys...")
    for u in confs['server']['users']:
        ssh_key = u['ssh_key']
        value = "\'0,/--SSH KEY HERE--/s//{}/\'".format(ssh_key)
        subprocess.Popen(["sed", value, "./ec2_boot_confs.sh"], shell=True)
# end get_ssh_keys()

def init_scripts():
    try:
        return open('./ec2_boot.sh', 'r').read()
    except Exception:
        print("\tNo users loaded! Send ec2_boot.sh to the instance after it's created.")
        return ""
# end init_scripts

def build_ze_instance(img_id: str, key_name: str, confs):
    global security_group, min_count, max_count, ec2

    try:  # get and use default VPC for instance
        default_vpc = list(ec2.vpcs.filter(Filters=[{
                    'Name': 'isDefault', 'Values': ['true']
                }]
        ))[0]
        print("Set default VPC:", default_vpc.id)
    except ClientError as e:
        print("\tCould not get VPCs!", e)
        force_quit()
    except IndexError as e:
        print(e)
        force_quit()

    group_name = 'ec2_fetch2_py'
    group_desc = 'ec2_fetch2_py_desc'
    try:  # set Security Group for instance
        security_group = default_vpc.create_security_group(GroupName=group_name, Description=group_desc)
        print("Created security group '{}' in VPC '{}'".format(group_name, default_vpc.id))
    except ClientError as e:
        print("Could not create security group: {}. {}".format(group_name, e))
        force_quit()

    try:  # set permissions
        ip_permissions = [{
            'IpProtocol': 'tcp', 'FromPort': 80, 'ToPort': 80,
            'IpRanges': [{'CidrIp': '0.0.0.0/0'}]
            }, {
            'IpProtocol': 'tcp', 'FromPort': 443, 'ToPort': 443,
            'IpRanges': [{'CidrIp': '0.0.0.0/0'}]
            }, {
            'IpProtocol': 'tcp', 'FromPort': 22, 'ToPort': 22,
            'IpRanges': [{'CidrIp': '0.0.0.0/0'}]
        }]
        security_group.authorize_ingress(IpPermissions=ip_permissions)
        print("\tSet security rules for '{}' to allow public access.".format(security_group.id))
    except ClientError as e:
        print("\tCould not authorize security rules for {}. {}".format(group_name, e))
        force_quit()

    try:  # load params for instance
        blk_dev_map = []

        # add volumes
        print("Loading volumes...")
        for v in confs['server']['volumes']:
            blk_dev_map.append({
                'DeviceName': v['device'],
                'Ebs': { 'VolumeSize': int(v['size_gb']) }
            })

        print("Loading users...")
        params={
            'ImageId': img_id,
            'InstanceType': inst_type,
            'KeyName': key_name,
            'SecurityGroupIds': [security_group.id],
            'UserData': init_scripts(),
            'BlockDeviceMappings': blk_dev_map
        }
        print("Creating instances...")
        instance = ec2.create_instances(**params, MinCount=min_count, MaxCount=max_count)
    except ClientError as e:
        print("\tCould not create instance!", e)
        force_quit()
    else:  # UX sleep, allow for instances to start
        print("Instances created. Initializing...")
        time.sleep(30)
# end build_ze_instance()

# do the thing
if __name__ == '__main__':
    print('Please standby...')

    # sanitize, avoid needless death
    if (str(sys.argv[1]).find('yml') != -1):
        key_file = str(sys.argv[2])
        yaml_file = str(sys.argv[1])
    elif (str(sys.argv[2]).find('yml') != -1):
        key_file = str(sys.argv[1])
        yaml_file = str(sys.argv[2])
    else:
        print("Provide configuraiton file or key file name!")
        force_quit()

    global ec2
    ec2 = boto3.resource('ec2')

    try:  # create and capture key, store locally as file
        key_pair = ec2.create_key_pair(KeyName=key_file)
        ec2_pem = open("./" + key_file + '.pem', 'w')
        ec2_pem.write(key_pair.key_material)
        ec2_pem.close()
        print("Key pair created.")
    except Exception as e:
        print("Cannot create keys!", e)
        force_quit()
    
    try:  # read yaml for confs
        conf_yaml = open("./" + yaml_file, 'r')
        ec2_confs = yaml.load(conf_yaml, Loader=yaml.FullLoader)
        conf_yaml.close()                   # done with file
        get_goodies(ec2_confs, yaml_file)   # parse file
        get_ssh_keys(ec2_confs)
    except ValueError as e:
        print("\tSomething went wrong:", e)
        force_quit()

    build_ze_instance(find_ami(), key_file, ec2_confs)
        
    print("EC2 instances were launched! Confirm in the AWS Console.")