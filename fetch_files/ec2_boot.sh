#!/bin/bash
# Create users for EC2 instance
sudo adduser user1
sudo su - user1
mkdir ~/.ssh && chmod 700 ~/.ssh
touch ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys
echo "--SSH KEY HERE--" >  ~/.ssh/authorized_keys
exit
sudo adduser user2
sudo su - user2
mkdir ~/.ssh && chmod 700 ~/.ssh
touch ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys
echo "--SSH KEY HERE--" >  ~/.ssh/authorized_keys
exit

