#!/bin/sh
imageName=$(cat IMAGENAME)
containerName=$(cat CONTAINERNAME)
sudo docker rm $containerName
sudo docker build \
	-t $imageName \
	-f ./postgresql.dockerfile ./

sudo docker run \
	--name $containerName \
	-p "127.0.0.1:5432:5432" \
	-v /taxed/pgdata:/var/lib/postgresql/data \
	$imageName
