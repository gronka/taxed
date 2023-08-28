#!/bin/sh

# -m creates home dir if not exists
useradd -m \
	-d /home/username \
	-s /bin/bash \
	-G sudo,wheel \
	username
