#!/bin/bash

check_result () {
    ___RESULT=$?
    if [ $___RESULT -ne 0 ]; then
        echo $1
        exit 1
    fi
}

source ../../prod-venv/bin/activate

set -a
export HCLOUD_TOKEN=$(yq -r .hcloud_token vars/hcloud_token.yml)

EXTRA_VARS="{ \"swarmsible_vars_path\": \"$(realpath vars)\", \"CWD\": \"$(pwd)\" }"

ansible-playbook -i inventory/ ./swarmsible/swarmsible-hetzner/swarmsible-hetzner/setup.yml --extra-vars="$EXTRA_VARS"
check_result "failed to setup hetzner nodes"

ansible-playbook -i inventory ./swarmsible/swarmsible/swarmsible/ansible_setup.yml --extra-vars="$EXTRA_VARS"
check_result "failed to run ansible_setup"

ansible-playbook -i inventory ./swarmsible/swarmsible/swarmsible/docker_swarm.yml --extra-vars="$EXTRA_VARS"
check_result "failed to run docker_swarm"

ansible-playbook -i inventory ./swarmsible/swarmsible/swarmsible/developer_accounts.yml --extra-vars="$EXTRA_VARS"
check_result "failed to run developer_accounts"