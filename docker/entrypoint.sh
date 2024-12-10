#!/bin/bash
set -e

export USER=bear
CONTAINER_UID=${UID:-1000}
CONTAINER_GID=${GID:-1000}
groupmod -o -g "$CONTAINER_GID" $USER
usermod -o -u "$CONTAINER_UID" $USER
chown -R $USER:$USER /app

exec su $USER -c "$@"

