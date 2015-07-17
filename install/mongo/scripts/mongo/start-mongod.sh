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

function get_response_code() {

    port=$1

    set +e

    curl_cmd=$(which curl)
    wget_cmd=$(which wget)

    if [[ ! -z ${curl_cmd} ]]; then
        response_code=$(curl -s -o /dev/null -w "%{http_code}" http://${port})
    elif [[ ! -z ${wget_cmd} ]]; then
        response_code=$(wget --spider -S "http://${port}" 2>&1 | grep "HTTP/" | awk '{print $2}' | tail -1)
    else
        ctx logger error "Failed to retrieve response code from http://localhost:${port}: Neither 'cURL' nor 'wget' were found on the system"
        exit 1;
    fi

    set -e

    echo ${response_code}

}

function wait_for_server() {

    ip=$1
    port=$2
    server_name=$3

    started=false

    ctx logger info "Running ${server_name} liveness detection on port ${port}"

    for i in $(seq 1 120)
    do
        response_code=$(get_response_code "${ip}:${port}")
        ctx logger info "[GET] http://${ip}:${port} ${response_code}"
        if [ ${response_code} -eq 200 ] ; then
            started=true
            break
        else
            ctx logger info "${server_name} has not started. waiting..."
            sleep 1
        fi
    done
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
IP=$(ctx instance host_ip)
RSET_NAME=$(ctx node properties rsetname)
MONGO_ROOT_PATH=$(ctx instance runtime_properties mongo_root_path)
MONGO_BINARIES_PATH=$(ctx instance runtime_properties mongo_binaries_path)
MONGO_DATA_PATH=$(ctx instance runtime_properties mongo_data_path)
COMMAND="${MONGO_BINARIES_PATH}/bin/mongod --bind_ip ${IP} --port ${PORT} --dbpath ${MONGO_DATA_PATH} --rest --journal --shardsvr"

if [ -n "${RSET_NAME}" ]; then
  COMMAND="${COMMAND} --replSet ${RSET_NAME}"
  ctx instance runtime_properties replicaset_name ${RSET_NAME}
fi

ctx logger info "db instance port: $PORT"

ctx instance runtime_properties mongo_port $PORT

ctx logger info "${COMMAND}"
nohup ${COMMAND} > /tmp/$(ctx instance id) 2>&1 &
PID=$!

MONGO_REST_PORT=`expr ${PORT} + 1000`
wait_for_server ${IP} ${MONGO_REST_PORT} 'MongoDB'

# this runtime porperty is used by the stop-mongo script.
ctx instance runtime_properties pid ${PID}

ctx logger info "Sucessfully started MongoDB (${PID})"
