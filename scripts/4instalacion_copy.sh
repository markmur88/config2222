#!/bin/bash

# Configuración de repositorios
sudo sh -c 'echo "deb [arch=amd64] https://deb.debian.org/debian/ bullseye main non-free contrib" >> /etc/apt/sources.list'
sudo sh -c 'echo "deb-src [arch=amd64] https://deb.debian.org/debian/ bullseye main non-free contrib" >> /etc/apt/sources.list'
sudo wget -q -O - https://archive.kali.org/archive-key.asc | apt-key add
sudo apt-get install -y kali-archive-keyring

# Actualización del sistema
sudo apt-get update
sudo apt-get upgrade -y
sudo apt-get autoremove -y
sudo apt-get clean

# Instalación de utilidades básicas
sudo apt-get install -y testdisk gnome-disk-utility gsettings-desktop-schemas gcc-9-base myspell-es

# Instalación de aplicaciones de escritorio
sudo apt-get install -y gimp inkscape telegram-desktop vlc qbittorrent filezilla

# Instalación de herramientas de desarrollo
sudo apt-get install -y npm default-jdk default-jre

# Instalación de ProtonVPN
wget https://repo.protonvpn.com/debian/dists/stable/main/binary-all/protonvpn-stable-release_1.0.8_all.deb
sudo dpkg -i ./protonvpn-stable-release_1.0.8_all.deb && sudo apt update
echo "0b14e71586b22e498eb20926c48c7b434b751149b1f2af9902ef1cfe6b03e180 protonvpn-stable-release_1.0.8_all.deb" | sha256sum --check -
sudo apt-get install -y proton-vpn-gnome-desktop libayatana-appindicator3-1 gir1.2-ayatanaappindicator3-0.1 gnome-shell-extension-appindicator

# Instalación de GitHub Desktop
wget -qO - https://apt.packages.shiftkey.dev/gpg.key | gpg --dearmor | sudo tee /usr/share/keyrings/shiftkey-packages.gpg > /dev/null
sudo sh -c 'echo "deb [arch=amd64 signed-by=/usr/share/keyrings/shiftkey-packages.gpg] https://apt.packages.shiftkey.dev/ubuntu/ any main" > /etc/apt/sources.list.d/shiftkey-packages.list'
sudo apt-get update && sudo apt-get install -y github-desktop

# Configuración de UFW
sudo apt-get install -y ufw
sudo ufw default allow incoming
sudo ufw default allow outgoing
sudo ufw logging full
sudo ufw enable

# Instalación de Docker
sudo apt-get install -y docker.io
sudo systemctl enable docker --now
sudo usermod -aG $USER
echo "deb [arch=amd64 signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/debian bullseye stable" | sudo tee /etc/apt/sources.list.d/docker.list 
curl -fsSL https://download.docker.com/linux/debian/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io
sudo usermod -aG Docker $USER
sudo systemctl enable docker
sudo systemctl start docker

# Instalación de PostgreSQL
sudo apt-get install -y postgresql postgresql-contrib
sudo systemctl enable postgresql
sudo systemctl start postgresql

sudo -u postgres psql <<EOF
CREATE USER markmur88 WITH PASSWORD 'Ptf8454Jd55';
ALTER USER markmur88 WITH SUPERUSER;
GRANT USAGE, CREATE ON SCHEMA public TO markmur88;
GRANT ALL PRIVILEGES ON SCHEMA public TO markmur88;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON FUNCTIONS TO markmur88;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO markmur88;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO markmur88;
DROP DATABASE IF EXISTS mydatabase;
CREATE DATABASE mydatabase;
GRANT ALL PRIVILEGES ON DATABASE mydatabase TO markmur88;
GRANT CONNECT ON DATABASE mydatabase TO markmur88;
GRANT CREATE ON DATABASE mydatabase TO markmur88;
EOF

# Instalación de Visual Studio Code
sudo apt-get install -y wget gpg apt-transport-https
wget -qO- https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor > packages.microsoft.gpg
sudo install -D -o root -g root -m 644 packages.microsoft.gpg /etc/apt/keyrings/packages.microsoft.gpg
echo "deb [arch=amd64,arm64,armhf signed-by=/etc/apt/keyrings/packages.microsoft.gpg] https://packages.microsoft.com/repos/code stable main" | sudo tee /etc/apt/sources.list.d/vscode.list > /dev/null
rm -f packages.microsoft.gpg
sudo apt-get update
sudo apt-get install -y code gvfs libglib2.0-bin

# Instalación de Ngrok
wget https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-stable-linux-amd64.zip
unzip ngrok-stable-linux-amd64.zip
sudo mv ngrok /usr/local/bin/
ngrok config add-authtoken 2tHm3L72AsLuKCcTGCD9Y9Ztlux_7CfAq6i4MCuj1EUAfZFST

# Instalación de paquetes de Python
sudo pip install django pillow pymysql

# Instalación de Spotify
curl -sS https://download.spotify.com/debian/pubkey_C85668DF69375001.gpg | sudo gpg --dearmor --yes -o /etc/apt/trusted.gpg.d/spotify.gpg
echo "deb https://repository.spotify.com stable non-free" | sudo tee /etc/apt/sources.list.d/spotify.list
sudo apt-get update && sudo apt-get install spotify-client

# Limpieza final
sudo apt-get clean
sudo apt-get autoremove -y
sudo apt-get update
sudo apt-get upgrade -y
sudo apt-get clean
sudo apt-get autoremove -y

# Fin del script
reboot
