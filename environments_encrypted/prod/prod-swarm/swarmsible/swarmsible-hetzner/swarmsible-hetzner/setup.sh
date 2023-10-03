source venv/bin/activate

set -a
export HCLOUD_TOKEN=$(yq -r .hcloud_token vars/hcloud_token.yml)

ansible-playbook -i inventories/sample/ setup.yml --extra-vars='{ "swarmsible_vars_path": "vars" }'