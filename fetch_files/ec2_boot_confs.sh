#!/bin/bash
# Add SSM to mount drives
cd /tmp
sudo yum install -y https://s3.amazonaws.com/ec2-downloads-windows/SSMAgent/latest/linux_amd64/amazon-ssm-agent.rpm
# Create users for EC2 instance
sudo adduser user1 --disabled-password
sudo su - user1
mkdir .ssh && chmod 700 .ssh
touch .ssh/authorized_keys && chmod 600 .ssh/authorized_keys
echo "--SSH KEY HERE--" >  .ssh/authorized_keys
exit # end su for user1
sudo adduser user2 --disabled-password
sudo su - user2
mkdir .ssh && chmod 700 .ssh
touch .ssh/authorized_keys && chmod 600 .ssh/authorized_keys
echo "--SSH KEY HERE--" >  .ssh/authorized_keys
exit # end su for user2