#!/bin/bash
# This script mounts volumes it reads from a yaml file
# This needs to run first, to build a script that will be sent to run instances
num_dev=$(cat ./*.yml | shyaml get-value server.volumes |grep 'device' |wc -l)
i=0
for d in 0..$num_dev; do
	name=$(cat ./*.yml |shyaml get-value server.volumes.$i |grep 'device' |cut -d: -f2)
	type=$(cat ./*.yml | shyaml get-value server.volumes.$i |grep 'type' |cut -d: -f2)
	mount=$(cat ./*.yml | shyaml get-value server.volumes.$i |grep 'mount' |cut -d: -f2)
	((i++))
	cat >> ./ec2_boot.sh<<EOF
ls $name
if [ \$? -gt 0 ]; then
	sudo yum install xfsprogs
	sudo mkfs -t $type $name
fi
echo "n
p
1


w" | sudo fdisk $name
sudo partprobe $name
sudo mkdir $mount; sudo chmod 755 $mount
sudo mount $name $mount
EOF
done
