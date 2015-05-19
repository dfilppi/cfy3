#!/bin/bash

set -e

ctx source instance runtime_properties mongo_ip_address $(ctx target instance runtime_properties outputs.server_info.value.ip_address)
ctx source instance runtime_properties mongo_port $(ctx target instance runtime_properties outputs.server_info.value.port)
