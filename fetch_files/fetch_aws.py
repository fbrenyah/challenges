#!/usr/bin/python3
# Purpose:      Fetch Rewards Coding Assessment - Site Reliability Engineer
#               Spin up an EC2 instance, using confs from a yaml file, in default AZ
#               with multiple volumes and SSH users that can connect to the instance
# Date:         July 11, 2021
# Written by:   Frank Brenyah
#
# Use: python3 fetch_aws.py <yaml_file> <key_name>
# Ex: python3 fetch_aws.py ec2conf.yml ec2-keypair
#
import sys
import time
import subprocess
import boto3
from botocore.exceptions import ClientError
import yaml


def forceQuit():  # force a quit, the script has failed
    print("\tThis script cannot continue. Terminating!")
    sys.exit()


# end forceQuit()

def findAMI():
    print("Searching for AMI to use...")
    global ec2
    client = ec2.meta.client
    image = client.describe_images(
        Filters=[
            {
                'Name': 'architecture',
                'Values': [archType],
                'Name': 'root-device-type',
                'Values': [rootDevType],
                'Name': 'virtualization-type',
                'Values': [virtType],
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
    return image  # return the AMI JSON


# end findAMI()

def getInstance(img_id):
    global maxCount, ec2
    if maxCount < 5: # This value must be between 5 and 1000. 
        maxCount = 5
    else:
        pass

    client = ec2.meta.client
    instance = client.describe_instances(
        Filters=[
            {
                'Name': 'image-id',
                'Values': [img_id]
            },
        ],
        MaxResults=maxCount,
        DryRun=False
    )
    return instance  # return instance info JSON


# end getInstance()

def getGoodies(confs, file):
    print("Getting confs from:", file)
    try:
        global maxCount
        maxCount = confs['server']['max_count']
        global minCount
        minCount = confs['server']['min_count']
        global instType
        instType = confs['server']['instance_type']
        global amiType
        amiType = confs['server']['ami_type']
        global archType
        archType = confs['server']['architecture']
        global rootDevType
        rootDevType = confs['server']['root_device_type']
        global virtType
        virtType = confs['server']['virtualization_type']
    except Exception as e:
        print("Failed to get configurations!", e)

    print("\tAMI Type:", amiType)
    print("\tInstance Type:", instType)
    print("\tArchitecture Type:", archType)
    print("\tRoot Device Type:", rootDevType)


# end getGoodies()

def getSSHKeys(confs):
    print("Getting user SSH keys...")
    for u in confs['server']['users']:
        ssh_key = u['ssh_key']
        value = "\'0,/--SSH KEY HERE--/s//{}/\'".format(ssh_key)
        subprocess.Popen(
            [
                "sed",
                value,
                "./ec2_boot_confs.sh"
            ],
            shell=True
        )


# end getSSHKeys()

def initScripts():
    try:
        return open('./ec2_boot.sh', 'r').read()
    except Exception as e:
        print("\t'Could not load users!", e)
        forceQuit()


# end initScripts

def buildZeInstance(img_id, key_name, confs):
    global security_group, minCount, maxCount, ec2

    try:  # get and use default VPC for instance
        default_vpc = list(ec2.vpcs.filter(
            Filters=[
                {
                    'Name': 'isDefault',
                    'Values': ['true']
                }
            ]
        ))[0]
        print("Got default VPC:", default_vpc.id)
    except ClientError as e:
        print("\tCould not get VPCs!", e)
        forceQuit()
    except IndexError as e:
        print(e)
        forceQuit()

    group_name = 'ec2_fetchrewards_py2'
    group_desc = 'ec2_fetchrewards_py2_desc'
    try:  # get and use default Security Group for instance
        security_group = default_vpc.create_security_group(
            GroupName=group_name,
            Description=group_desc
        )
        print("Created security group '{}' in VPC '{}'".format(group_name, default_vpc.id))
    except ClientError as e:
        print("Could not create security group: {}. {}".format(group_name, e))
        forceQuit()

    try:  # set permissions
        ip_permissions = [{  # HTTP ingress open to anyone
            'IpProtocol': 'tcp', 'FromPort': 80, 'ToPort': 80,
            'IpRanges': [{'CidrIp': '0.0.0.0/0'}]}, {  # HTTPS ingress open to anyone
            'IpProtocol': 'tcp', 'FromPort': 443, 'ToPort': 443,
            'IpRanges': [{'CidrIp': '0.0.0.0/0'}]
        }, {
            # SSH ingress open to anyone
            'IpProtocol': 'tcp', 'FromPort': 22, 'ToPort': 22,
            'IpRanges': [{'CidrIp': '0.0.0.0/0'}]}]
        security_group.authorize_ingress(IpPermissions=ip_permissions)
        print("\tSet security rules for '{}' to allow public access.".format(security_group.id))
    except ClientError as e:
        print("\tCould not authorize security rules for {}. {}".format(group_name, e))
        forceQuit()

    try:  # load params for instance, add volume based on conf
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
            'InstanceType': instType,
            'KeyName': key_name,
            'SecurityGroupIds': [security_group.id],
            'UserData': initScripts(),
            'BlockDeviceMappings': blk_dev_map
        }
        # end add volumes

        print("Creating instances...")
        instance = ec2.create_instances(
            **params,
            MinCount=minCount,
            MaxCount=maxCount
        )
        print("Instances created. Initializing...")
    except ClientError as e:
        print("\tCould not create instance!", e)
        forceQuit()
    else:  # allow time for instances and volumes to start
        time.sleep(45)


# end buildZeInstance()

def startZeInstance(inst_id): #unused for now
    global ec2
    instance = ec2.Instance(inst_id)
    try:
        instance.start()
        print("Starting instance, standby...")
    except Exception as e:
        print("\tFailed to start instance!", e)
        forceQuit()
    else:
        time.sleep(30)


# end startZeInstance()

# do the thing
if __name__ == '__main__':
    print('Please standby...')

    yaml_file = str(sys.argv[1])
    key_file = str(sys.argv[2])

    global ec2
    ec2 = boto3.resource('ec2')

    try:  # capture the key and store it in a file
        key_pair = ec2.create_key_pair(KeyName=key_file)
        ec2Pem = open("./" + key_file + '.pem', 'w')
        ec2Pem.write(key_pair.key_material)
        ec2Pem.close()
        print("Key pair created.")
    except Exception as e:
        print("Cannot create keys!", e)
        forceQuit()
    
    try:  # Get yaml to read confs
        ec2ConfYaml = open("./" + yaml_file, 'r')
        ec2confs = yaml.load(ec2ConfYaml, Loader=yaml.FullLoader)
        ec2ConfYaml.close()
        getGoodies(ec2confs, yaml_file)  # parse file
        getSSHKeys(ec2confs)
    except ValueError as e:
        print("\tSomething went wrong:", e)
        forceQuit()

    ami_id = findAMI()
    buildZeInstance(ami_id, key_file, ec2confs)
        
    print("EC2 instances were launched! Confirm in the AWS Console.")