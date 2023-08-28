#!/bin/sh
containerName=$(cat docker/CONTAINERNAME)
sudo docker start $containerName
