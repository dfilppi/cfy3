#!/bin/bash

set -e

function next_port(){
  local sport=$1
  set +e
  
  while [ true ]; do
    sudo netstat -ln | grep "tcp " | grep -q ":${sport} "
    if [ $? -ne 0 ]; then
      echo ${sport}
      set -e
      return 0
    else
      sport=$((${sport} + 1))
      if [ ${sport} -eq 65535 ]; then
        set -e
        return -1
      fi
    fi  
  done
}

# simple "port listening" implementation
function wait_for_server() {

    local port=$1
    local server_name=$2

    local started=false

    set +e

    ctx logger info "Running ${server_name} liveness detection on port ${port}"

    for i in $(seq 1 120)
    do
        sudo netstat -ln | grep "tcp " | grep -q ":${port} "
        local ret=$?

        if [ $ret -eq 0 ] ; then
            started=true
            break
        else
            ctx logger info "${server_name} has not started. waiting..."
            sleep 1
        fi
    done
    set -e
    if [ ${started} = false ]; then
        ctx logger error "${server_name} failed to start. waited for a 120 seconds."
        exit 1
    fi
}

PORT=$(ctx node properties port)
#get available port
PORT=$(next_port ${PORT})

ctx logger info "cfg instance port: $PORT"

ctx instance runtime_properties mongo_port $PORT


#IP=$(ctx instance host_ip)
IP=192.168.33.11
INSTANCEID=$(ctx instance id)
MONGO_ROOT_PATH=$(ctx instance runtime_properties mongo_root_path)
MONGO_BINARIES_PATH=$(ctx instance runtime_properties mongo_binaries_path)
MONGO_DATA_PATH=$(ctx instance runtime_properties mongo_data_path)
COMMAND="${MONGO_BINARIES_PATH}/bin/mongod --configsvr --bind_ip ${IP} --port ${PORT} --dbpath ${MONGO_DATA_PATH}"

ctx logger info "${COMMAND}"
nohup ${COMMAND} > "/tmp/${INSTANCEID}_start" 2>&1 &
PID=$!

MONGO_REST_PORT=`expr ${PORT} + 1000`
wait_for_server ${MONGO_REST_PORT} 'MongoDB'

# this runtime porperty is used by the stop-mongo script.
ctx instance runtime_properties pid ${PID}

ctx logger info "Successfully started MongoC (${PID})"
