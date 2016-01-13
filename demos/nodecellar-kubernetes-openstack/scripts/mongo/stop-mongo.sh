#!/bin/bash

set -e

PID=$(ctx instance runtime_properties pid)

if [ -z "${PID}" ]; then
  exit 0
fi

kill -9 ${PID}

ctx logger info "Sucessfully stopped MongoDB (${PID})"
