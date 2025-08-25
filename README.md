# Fix: Rapoo M50 (Plus/Silent) Back/Forward buttons on Linux

**TL;DR:** A tiny userspace bridge that reads the Rapoo dongle’s raw HID reports and emits proper Back/Forward (or Alt+Left/Alt+Right) key events. Works on X11/Wayland, KDE/GNOME, etc.

- Tested device: **Rapoo M50 Plus Silent** (USB VID:PID **24ae:2015**)
- Kernel sees the mouse but doesn’t surface side buttons → this tool fills the gap.
- Zero kernel patching. Uses `hidraw` + `uinput`.

## Features
- Listens to all Rapoo hidraw interfaces (handles multi-interface dongles).
- Two modes:
  - `backforward` → sends `KEY_BACK` / `KEY_FORWARD`
  - `altarrow` → sends `Alt+Left` / `Alt+Right` (universal fallback)

## Requirements
- Python 3, `python3-evdev`
- Access to `/dev/hidraw*` and `/dev/uinput` (root or proper udev rules)
- Linux kernel ≥ 5.x (tested on 6.14)


## Install (TL;DR)
```bash
chmod +x ./install.sh
sudo ./install.sh
```

## Install (manual)
```bash
sudo apt update
sudo apt install -y python3-evdev

# Clone
git clone https://github.com/khalifmahdi/rapoo-m50-linux-fix.git
cd rapoo-m50-linux-fix

# Install script
sudo install -Dm755 src/rapoo_m50_sidebuttons.py /usr/local/bin/rapoo-m50-sidebuttons

# Quick test
sudo RAPOO_DEBUG=1 /usr/local/bin/rapoo-m50-sidebuttons
# Press Back/Forward on the mouse; you should see mask=0x10 / mask=0x08
# Try in your browser; if nothing happens, run in fallback mode:
sudo RAPOO_MODE=altarrow /usr/local/bin/rapoo-m50-sidebuttons

# Autostart (systemd)
sudo install -Dm644 systemd/rapoo-m50-sidebuttons.service /etc/systemd/system/rapoo-m50-sidebuttons.service
# Optional: choose mode (backforward or altarrow)
sudo systemctl edit rapoo-m50-sidebuttons.service
# Add:
# [Service]
# Environment=RAPOO_MODE=altarrow

sudo systemctl daemon-reload
sudo systemctl enable --now rapoo-m50-sidebuttons.service
systemctl status rapoo-m50-sidebuttons.service --no-pager

# Running as non-root (optional)
# Grant your user access to uinput/hidraw (varies by distro). Example udev rule:
cat <<'U' | sudo tee /etc/udev/rules.d/70-rapoo-sidebuttons.rules
KERNEL=="uinput", MODE="0660", GROUP="input"
SUBSYSTEM=="hidraw", ATTRS{idVendor}=="24ae", ATTRS{idProduct}=="2015", MODE="0660", GROUP="input"
U
sudo udevadm control --reload && sudo udevadm trigger
sudo usermod -aG input $USER
# Reboot or re-login, then change the systemd unit to User=$USER
```

## Uninstall
sudo systemctl disable --now rapoo-m50-sidebuttons.service
sudo rm -f /etc/systemd/system/rapoo-m50-sidebuttons.service
sudo rm -f /usr/local/bin/rapoo-m50-sidebuttons

## Troubleshooting

No reaction in browser: run with `RAPOO_DEBUG=1` and verify you see mask=0x10 / mask=0x08 when pressing the buttons.

Still no nav: set RAPOO_MODE=altarrow (universal).

Multiple hidraw nodes: the tool listens to all Rapoo hidraw interfaces; you should still see debug masks.