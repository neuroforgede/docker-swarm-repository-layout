rm -rf swarmsible
mkdir -p swarmsible
cd swarmsible
git clone --single-branch --branch 22.11.3 https://github.com/neuroforgede/swarmsible.git
rm -rf swarmsible/.git
git clone --single-branch --branch 23.02.1 https://github.com/neuroforgede/swarmsible-hetzner.git
rm -rf swarmsible-hetzner/.git