#!/bin/sh
containerName=$(cat docker/CONTAINERNAME)
sudo docker stop $containerName
