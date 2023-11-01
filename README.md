# Introduction 

To understand the structure of this repository, it is important to understand the concept of environments. Environments can be stages of a SaaS app, or just different areas that you want to manage separately. You can specify per environment who has access to it and who doesn't. This is done by encrypting the environment with the public keys of the people who should have access to it.

A common pattern here is to have one environment per Docker Swarm you manage. This way you can have different people manage different swarms without them having access to the secrets of the other swarms. Also, often times you will also have to manage the database cluster in the same environment. Depending on your wants,
you could then add the database cluster to the same environment as the Docker Swarm, or you could create a separate environment for the database cluster.

To keep things simple however this will focus on the Docker Swarm specifics of this style of repository management, as this is arguably the most interesting bit.

# High-Level Explanation of folders

The layout of this repository is as follows:
    
    ├── age
    │   ├── amd64
    │   └── arm64
    ├── backup
    │   ├── decrypted
    │   └── encrypted
    ├── environments
    │   ├── prod
    │   └── prod-venv
    ├── environments_encrypted
    │   └── prod
    ├── README.md
    ├── secrets.py
    └── stack_templates
        ├── ...

## secrets.py

This python script handles the encryption and decryption of the environments. It is intentionally kept simple and essentially handles copying between environments and environments_encrypted via the commands `encrypt` and `decrypt`  respectively.

Secrets are detected by convention. Essentially, any file with the word `secret` in its path (together with some other common secret files) is treated as private and is automatically encrypted/decrypted.

Example of a workflow using secrets.py:

```
1. git checkout branch
2. ./secrets.py decrypt <env>
3. make changes to environment
4. ./secrets.py encrypt <env>
5. git commit
```

## age

This folder contains the age binary for all relevant architectures. [Age](https://github.com/FiloSottile/age) is a simple, modern and secure file encryption tool. Currently supported are amd64 and arm64.
While the binaries could be downloaded from the internet, it should be fine to have them in the repository as they are rather small.

## backup

This folder contains backups of both the encrypted and the decrypted environment folders. This is to ensure that during development you don't lose any data because of mistakes when working with secrets.py.

This folder is not encrypted and must be kept out of git.

## environments

This folder contains all environments. Environments are the "atomic" unit of encryption management. You can specify per environment who has access to it and who doesn't. This is done by encrypting the environment with the public keys of the people who should have access to it.

The unencrypted version of the environment is stored in the environments folder. The encrypted version of it is stored in the environments_encrypted folder. The unencrypted version has to be kept out of git. The encrypted version is the one to be checked in.

## environments_encrypted

This folder contains the encrypted versions of the environments.

## stack_templates

This folder contains the stack templates. These are the files that are used to create the docker stacks. For building stack templates we use [nothelm.py](https://github.com/neuroforgede/nothelm-charts) for templating. Most of these stack templates also make use of [docker-stack-deploy](https://github.com/neuroforgede/docker-stack-deploy) for automatic config and secret rotation.


# Anatomy of an environment

```
├── age_recipients.txt
├── prod-swarm
│   ├── bin
│   ├── files
│   ├── firewall.sh
│   ├── install_dependencies.sh
│   ├── inventory
│   ├── secrets
│   ├── setup.sh
│   ├── ssh_keys
│   ├── stacks
│   ├── swarmsible
│   ├── upgrade.sh
│   ├── user_accounts.sh
│   ├── vars
│   └── vendor_swarmsible.sh
```

At the top level of any environment you have to place a file called `age_recipients.txt`. This file contains the public ssh keys of the people who should have access to the environment. The file should look like this:

```txt
<public key 1> <public key name 1>

<public key 2> <public key name 2>
...
```

## swarm folder

### bin

This folder contains utility scripts to work with the docker swarm on your CLI. Currently this contains only an `activate` script which can be used to automatically set up a DOCKER_HOST environment variable so that you can point your local docker cli to the remote docker swarm.

### files/all/ssh_files/developer_ssh_keys

This contains all public ssh keys of users that should have remote access to the swarm. This does not necessarily have to be the same as the contents of the age_recipients.txt. Note that these ssh keys also have to be set up in the inventory setup in order to be picked up.

### inventory

This contains the Swarmsible Ansible inventory. Note that we only use Ansible to manage the infrastructure but
not to deploy into the Docker Swarm. This is done exclusively via the scripts in the `stacks` folder.

### secrets

Any additional secrets that might be relevant to the environment can be placed here. This is optional.

### ssh_keys

All relevant SSH keys for usage by Ansible. This is usually a root SSH key and an ansible SSH key. This folder is via secrets.py.

### stacks

This contains all stacks that should be deployed to the environment. Stack folders are sorted lexicographically by the order in which they should be deployed in case of a full redeploy. This is important because some stacks might depend on others. For example, you might want to deploy a database cluster before deploying the app that uses it.

Example layout:

```
.
├── 00_docker_socket_proxy
│   └── deploy.sh
├── 00_hetzner-volumes
│   ├── deploy.sh
│   └── overrides
├── 01_cleanup
│   └── deploy.sh
├── 01_traefik_public
│   ├── deploy.sh
│   ├── secrets
│   └── values.yaml
├── 02_monitoring
│   ├── deploy.sh
│   ├── secrets
│   └── values.yaml
├── 02_portainer
│   ├── deploy.sh
│   └── values.yaml
├── 03_bookstack
│   ├── deploy.sh
│   ├── secrets
│   └── values.yaml
├── 03_passbolt
│   ├── configs
│   ├── deploy.sh
│   ├── passbolt.yml
│   └── secrets
├── deploy_all.sh
└── README.md
```

Note that every stack has a `deploy.sh` script by convention. This script usually looks something like this:

```bash
#!/bin/bash
exec nothelm run deploy --project-dir ../../../../../stack_templates/02_monitoring -f values.yaml -f secrets/secret_values.yaml
```

Essentially, inside a given environment we try to avoid having to write any stacks instead we only configure the stack_templates at the root of the repository with values as well as secret values similar to how we would do that with helm. To run the deploy we then usually just use nothelm to tie everything together.
