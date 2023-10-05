rm -rf ../../prod-venv
python3 -m venv ../../prod-venv
source ../../prod-venv/bin/activate

pip3 install ansible==6.5.0
pip3 install hcloud==1.18.0
pip3 install yq
pip3 install https://github.com/neuroforgede/docker-stack-deploy/archive/refs/tags/0.2.12.zip
ansible-galaxy collection install hetzner.hcloud:==1.9.1
