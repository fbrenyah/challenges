#!/bin/bash
# This script mounts volumes it reads from a yaml file
# This needs to run first, to build a script that will be sent to run instances
# This also copies the aws keys to the local directory
cp ~/.aws/credentials ./aws_creds
touch ./mount_volumes.sh
printf "#!/bin/bash \n" >> ./mount_volumes.sh
num_dev=$(cat ./*.ml | shyaml get-value server.volumes |grep 'device' |wc -l)
i=0
for d in 0..$num_dev; do
	name=$(cat ./*ml |shyaml get-value server.volumes.$i |grep 'device' |cut -d: -f2)
	type=$(cat ./*.ml | shyaml get-value server.volumes.$i |grep 'type' |cut -d: -f2)
	mount=$(cat ./*.ml | shyaml get-value server.volumes.$i |grep 'mount' |cut -d: -f2)
	((i++))
	cat >> ./mount_volumes.sh <<EOF
	sudo mkfs -t $type $name
	if \$? > 0
		sudo yum install xfsprogs
		sudo mkfs -t $type $name
	sudo mkdir $mount
	if \$? == 0
		sudo mount $name $mount
EOF
done
chmod +rx ./mount_volumes.sh