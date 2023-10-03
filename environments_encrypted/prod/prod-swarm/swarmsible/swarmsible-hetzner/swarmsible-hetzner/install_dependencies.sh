rm -rf venv
python3 -m venv venv
source venv/bin/activate

pip3 install ansible==6.5.0
pip3 install hcloud==1.18.0
pip3 install yq
ansible-galaxy collection install hetzner.hcloud:==1.8.2