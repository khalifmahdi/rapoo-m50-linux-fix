#!/bin/bash

sudo apt update
sudo apt install -y python3-evdev

git clone https://github.com/khalifmahdi/rapoo-m50-linux-fix.git

cd rapoo-m50-linux-fix
sudo install -Dm755 src/rapoo_m50_sidebuttons.py /usr/local/bin/rapoo-m50-sidebuttons
sudo install -Dm644 systemd/rapoo-m50-sidebuttons.service /etc/systemd/system/rapoo-m50-sidebuttons.service

sudo systemctl daemon-reload
sudo systemctl enable --now rapoo-m50-sidebuttons.service

systemctl status rapoo-m50-sidebuttons.service --no-pager
