#!/bin/bash
sudo sh -c 'echo "deb [arch=amd64] https://deb.debian.org/debian/ bullseye main non-free contrib" >> /etc/apt/sources.list'
sudo sh -c 'echo "deb-src [arch=amd64] https://deb.debian.org/debian/ bullseye main non-free contrib" >> /etc/apt/sources.list'

sudo wget -q -O - https://archive.kali.org/archive-key.asc | apt-key add
sudo apt-get install -y kali-archive-keyring


sudo apt-get update
sudo apt-get upgrade -y
sudo apt-get autoremove -y
sudo apt-get clean

sudo apt-get install -y testdisk
sudo apt-get install -y gnome-disk-utility
sudo apt-get install -y gsettings-desktop-schemas
sudo apt-get install -y gcc-9-base
sudo apt-get install -y myspell-es
sudo apt-get install -y gimp
sudo apt-get install -y inkscape
sudo apt-get install -y telegram-desktop
sudo apt-get install -y vlc
sudo apt-get install -y qbittorrent
sudo apt-get install -y proftpd
sudo apt-get install -y filezilla
sudo apt-get install -y npm
sudo apt-get install -y default-jdk
sudo apt-get install -y default-jre

# PROTON VPN
wget https://repo.protonvpn.com/debian/dists/stable/main/binary-all/protonvpn-stable-release_1.0.8_all.deb
sudo dpkg -i ./protonvpn-stable-release_1.0.8_all.deb && sudo apt update
echo "0b14e71586b22e498eb20926c48c7b434b751149b1f2af9902ef1cfe6b03e180 protonvpn-stable-release_1.0.8_all.deb" | sha256sum --check -
sudo apt-get install proton-vpn-gnome-desktop
sudo apt-get install libayatana-appindicator3-1 gir1.2-ayatanaappindicator3-0.1 gnome-shell-extension-appindicator

# GITHUB DESKTOP
wget -qO - https://apt.packages.shiftkey.dev/gpg.key | gpg --dearmor | sudo tee /usr/share/keyrings/shiftkey-packages.gpg > /dev/null
sudo sh -c 'echo "deb [arch=amd64 signed-by=/usr/share/keyrings/shiftkey-packages.gpg] https://apt.packages.shiftkey.dev/ubuntu/ any main" > /etc/apt/sources.list.d/shiftkey-packages.list'
sudo apt-get update && sudo apt-get install github-desktop

# UFW
sudo apt-get install -y ufw
sudo ufw default allow incoming
sudo ufw default allow outgoing
sudo ufw logging full
sudo ufw enable

# DOCKER
sudo apt-get update
sudo apt-get install -y docker.io
sudo systemctl enable docker --now
sudo usermod -aG $USER
echo "deb [arch=amd64 signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/debian bullseye stable" | sudo tee /etc/apt/sources.list.d/docker.list 
curl -fsSL https://download.docker.com/linux/debian/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io

# POSTGRESQL
sudo apt-get update
sudo apt-get install postgresql postgresql-contrib -y
sudo systemctl enable postgresql
sudo systemctl start postgresql
sudo systemctl status postgresql


sudo -u postgres psql

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


# VSCODE
sudo apt-get install wget gpg
wget -qO- https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor > packages.microsoft.gpg
sudo install -D -o root -g root -m 644 packages.microsoft.gpg /etc/apt/keyrings/packages.microsoft.gpg
echo "deb [arch=amd64,arm64,armhf signed-by=/etc/apt/keyrings/packages.microsoft.gpg] https://packages.microsoft.com/repos/code stable main" |sudo tee /etc/apt/sources.list.d/vscode.list > /dev/null
rm -f packages.microsoft.gpg
sudo apt-get install apt-transport-https
sudo apt-get update
sudo apt-get install code
sudo snap install --classic code
sudo apt-get install gvfs libglib2.0-bin



# NGROK
wget https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-stable-linux-amd64.zip
unzip ngrok-stable-linux-amd64.zip
sudo mv ngrok /usr/local/bin/
ngrok config add-authtoken 2tHm3L72AsLuKCcTGCD9Y9Ztlux_7CfAq6i4MCuj1EUAfZFST




sudo pip install django
sudo pip install pillow
sudo pip install pymysql

sudo apt-get clean
sudo apt-get autoremove -y
sudo apt-get update
sudo apt-get upgrade -y
sudo apt-get clean
sudo apt-get autoremove -y
