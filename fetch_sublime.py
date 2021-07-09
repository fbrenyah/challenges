#!/usr/bin/python3
# Purpose:      Fetch Rewards Coding Assessment - Site Reliability Engineer
# Purpose:      Spin up an EC2 instance, using confs from a yaml file, in us-west-1
# Purpose:      with two volumes and two SSH users that can connect to the instance
# Date:         July 8, 2021
# Written by:   Frank Brenyah
#
# Use: python3 fetchrewards.py <yaml_file> <availability_zone> <key_name>
# Ex: python3 fetchrewards.py ec2conf.yml us-west-1 ec2-keypair
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
    client = ec2.meta.client
    image = client.describe_images(
        Filters=[
            {
                'Name': 'architecture',
                'Values': [archType],
                'Name': 'availability-zone',
                'Values': [availZone],
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
    global maxCount
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
    except:
        print("One or more of the EC2 config values was not found!")

    print("\tAvailability Zone:", availZone)
    print("\tAMI Type:", amiType)
    print("\tInstance Type:", instType)
    print("\tArchitecture Type:", archType)
    print("\tRoot Device Type:", rootDevType)


# end getGoodies()

# def getSSHKeys(file, confs):
def getSSHKeys(confs):
    for u in confs['server']['users']:
        print("Getting user SSH keys...")
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

def readyVolumes(confs):
    # must loop this for all possible instances
    print("Attempting to mount volumes...")
    client = ec2.meta.client
    response = client.describe_volumes(
        Filters=[
            {
                'Name': 'status',
                'Values': ['creating', 'available', 'in-use']
            }
        ],
        DryRun=False,
        MaxResults=len(confs['Volumes'].keys())  # is a value, may not be able to call keys() on it, needs to be dict
    )

    for v in response['Volumes']:
        print("\t---------------------Volume Info---------------------")
        print("\tID:", v['VolumeId'])
        print("\tName:", v['Attachments']['Device'])
        print("\tInstance:", v['Attachments']['InstanceId'])
        print("\tSize:", v['Size'])
        print("\tState:", v['State'])
        print("\tTime:", v['Attachments']['AttachTime'])

    # format and mount drives, needs script
    with open('~/.aws/credentials') as f:
        for line in f:
            if line.find('aws_access_key_id') != -1:
                aws_key = line.split(' = ', 1)[1]
            elif line.find('aws_secret_access_key') != -1:
                aws_secret = line.split(' = ', 1)[1]

            print("Received AWS API keys...")
            # build key config
            conn_args = {
                'aws_access_key_id': aws_key,
                'aws_secret_access_key': aws_secret,
                'region_name': availZone
            }

    ssm_client = boto3.client('ssm', **conn_args)

    instances = []
    outputs = list({})
    not_executed = list()

    commands = list({})  # a list of commands, one command per line
    with open('./mount_volumes.sh') as c:
        for line in c:
            commands.append(line)  # add command line by line to list

    # Instances that have active ssm agent
    if len(ssm_client.describe_instance_information()['InstanceInformationList']) > 0:
        ssm_response = ssm_client.describe_instance_information(MaxResults=maxCount)['InstanceInformationList']
        for i in ssm_response:
            instances.append(i['InstanceId'])

        ssm_response = ssm_client.send_command(
            DocumentName="AWS-RunShellScript",
            Parameters={
                'commands': [commands]
            },
            InstanceIds=instances,
            MaxErrors=maxCount,
            TimeoutSeconds=60
        )

        # get the command id
        com_id = ssm_response['Command']['CommandId']

        # Wait for commands to execute
        while True:
            list_comm = ssm_client.list_commands(CommandId=com_id)
            if list_comm['Commands'][0]['Status'] == 'Pending' or list_comm['Commands'][0]['Status'] == 'InProgress':
                continue
            else:  # Commands on all Instances were executed
                break

        # Get the ssm_responses from the instances
        for i in instances:
            ssm_response2 = ssm_client.get_command_invocation(CommandId=com_id, InstanceId=i)
            if ssm_response2['ResponseCode'] == -1:
                not_executed.append(i)
            else:
                outputs.append(
                    {
                        'instance_id': i,
                        'stdout': ssm_response2['StandardOutputContent'],
                        'stderr': ssm_response2['StandardErrorContent']
                    }
                )
            print(outputs[i])
    else:
        print("\tThere is no any available instance that has a working SSM service!")
        forceQuit()


# end readyVolumes

def addUsers():
    print('Attempting to add users to instance at boot...')
    try:
        return open('./ec2_boot_confs.sh', 'r').read()
    except:
        print("\t'Could' not read bash file ec2_boot_confs.sh to add users!")
        forceQuit()


# end addUsers

def buildZeInstance(img_id, key_name, confs):
    global security_group, availZone, minCount, maxCount

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
    except IndexError as i:
        print(i)
        forceQuit()

    group_name = 'ec2_fetchrewards_py'
    group_desc = 'ec2_fetchrewards_py_desc'
    try:  # get and use default Security Group for instance
        security_group = default_vpc.create_security_group(
            GroupName=group_name,
            Description=group_desc
        )
        print("Created security group '{}' in VPC '{}'...".format(group_name, default_vpc.id))
    except ClientError:
        print("\tCould not create security group: {}. {}".format(group_name, e))
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
        print("Set security rules for '{}' to allow public HTTP/S ".format(security_group.id))
    except ClientError as e:
        print("\tCould not authorize security rules for {}. {}".format(group_name, e))
        forceQuit()

    try:  # load params for instance, add volume based on conf
        blk_dev_map = []

        # add volumes
        for v in confs['server']['volumes']:
            blk_dev_map.append({
                'DeviceName': v['device'],
                'Ebs': {
                    'Iops': 1000,
                    'VolumeSize': int(v['size_gb']),
                }
            })

        params={
            'ImageId': img_id,
            'InstanceType': instType,
            'KeyName': key_name,
            'SecurityGroupIds': [security_group.id],
            'UserData': addUsers(),
            'BlockDeviceMappings': blk_dev_map,
            'Placement': { 'AvailabilityZone': availZone }
        }
        # end add volumes

        instance = ec2.create_instances(
            **params,
            MinCount=minCount,
            MaxCount=maxCount
        )
        print("Created instance. ID:", instance.id)
    except ClientError as e:
        print("\tCould not create instance!", e)
        #forceQuit()
    else:  # allow instance and volumes to start
        time.sleep(60)
        print("\tPlease allow for one minute for build to complete...")


# end buildZeInstance()

def startZeInstance(inst_id): #unused for now
    global ec2
    instance = ec2.Instance(inst_id)
    try:
        instance.start()
        print("Starting instance, standby...")
    except:
        print("\tFailed to start instance! Quitting...")
        forceQuit()
    else:
        time.sleep(30)


# end startZeInstance()

# do the thing
if __name__ == '__main__':
    # Setting vars for use across all functions
    print('Please standby...')

    n = len(sys.argv)
    for i in range(1,n):
        print('Arg #{}: {}'.format(i, sys.argv[i]))

    yaml_file = sys.argv[1]
    global availZone
    availZone = sys.argv[2]
    key_file = sys.argv[3]

    global ec2
    ec2 = boto3.resource('ec2', region_name=availZone)

    #print('Skipping keys for test...')
    try:  # capture the key and store it in a file
        key_pair = ec2.create_key_pair(KeyName=key_file)
        ec2Pem = open("./" + key_file + '.pem', 'w')
        ec2Pem.write(key_pair.key_material)
        ec2Pem.close()
        print("Key pair created...")
    except:
        print("Cannot create keys!")
        forceQuit()
    
    try:  # Get yaml to read confs
        ec2ConfYaml = open("./" + yaml_file, 'r')
        ec2confs = yaml.load(ec2ConfYaml, Loader=yaml.FullLoader)
        ec2ConfYaml.close()
        getGoodies(ec2confs, yaml_file)  # parse file
        #print("Skipping SSH Keys for test...")
        getSSHKeys(ec2confs)
    except ValueError as v:
        print("\tSomething went wrong:", v)
        forceQuit()

    ami_id = findAMI()
    buildZeInstance(ami_id, key_file, ec2confs)
    
    # add volumes to the running instance
    readyVolumes(ec2confs)
    
    ec2Instance = getInstance(ami_id)
    '''try:
        if ami_id is not None:
            safe=False
            if ec2Instance is not None:
                if ec2Instance['Reservations'][0] is not None:
                    safe=True
                    global maxCount
                    global instID
                    for x in range(maxCount):
                        # this next line needs to create a list of ids to displace instances
                        instID = ec2Instance['Reservations'][x]['Instances']['InstanceId']
                        if ec2Instance['instance-state-name'] == 'stopped' or ec2Instance['instance-state-name'] == 'terminated':
                            startZeInstance(instID)
    except ClientError as e:
        print("\tFailed to get instance ID for an instance!", e)
        forceQuit()

    if safe:
        global maxCount
        global instID
        for x in range(maxCount):
            instID = ec2Instance['Reservations'][x]['Instances']['InstanceId']
            # Instance created and ready for use
            print("\t---------------------Instance Created---------------------")
            print("\tInstance id:", instID)
            print("\tInstance public IP:", ec2Instance.public_ip_address)
            print("\tInstance private IP:", ec2Instance.private_ip_address)
            print("\tPublic dns name:", ec2Instance.public_dns_name)
            print("\t----------------------------------------------------------")'''