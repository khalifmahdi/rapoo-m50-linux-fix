
# src/rapoo_m50_sidebuttons.py
```python
#!/usr/bin/env python3
import os, sys, glob, time, fcntl
from evdev import UInput, ecodes as e

# Rapoo M50 Plus/Silent 2.4G dongle (lsusb: 24ae:2015)
VENDOR = '24AE'
PRODUCT = '2015'
MODE = os.environ.get('RAPOO_MODE', 'backforward')  # 'backforward' or 'altarrow'
DEBUG = os.environ.get('RAPOO_DEBUG', '0') == '1'

def parse_hid_id(hid_id: str):
    # Example: "0003:000024AE:00002015"
    parts = hid_id.strip().split(':')
    if len(parts) != 3: return None, None, None
    bus, vend, prod = parts
    vend = (vend.lstrip('0') or '0').upper()
    prod = (prod.lstrip('0') or '0').upper()
    bus  = (bus.lstrip('0')  or '0').upper()
    return bus, vend, prod

def find_candidates():
    """Return list of (devnode, name, hid_id) for Rapoo 24AE:2015 devices."""
    cands = []
    for dev in glob.glob('/sys/bus/hid/devices/*'):
        uevent = os.path.join(dev, 'uevent')
        if not os.path.exists(uevent): continue
        kv = {}
        with open(uevent, 'r') as f:
            for line in f:
                if '=' in line:
                    k, v = line.strip().split('=', 1)
                    kv[k] = v
        name  = kv.get('HID_NAME', '')
        hidid = kv.get('HID_ID', '')
        _, vend, prod = parse_hid_id(hidid) if hidid else (None, None, None)
        match_vp = (vend == VENDOR and prod == PRODUCT)
        match_nm = ('RAPOO' in name.upper() and 'RAPOO 2.4G WIRELESS DEVICE' in name.upper())
        if match_vp or match_nm:
            dr = os.path.join(dev, 'hidraw')
            if os.path.isdir(dr):
                for n in sorted(os.listdir(dr)):
                    if n.startswith('hidraw'):
                        cands.append(('/dev/'+n, name, hidid))
    return cands

def make_uinput():
    if MODE == 'altarrow':
        return UInput({ e.EV_KEY: [e.KEY_LEFTALT, e.KEY_LEFT, e.KEY_RIGHT] },
                      name='rapoo-m50-sidebuttons', bustype=0x03)
    return UInput({ e.EV_KEY: [e.KEY_BACK, e.KEY_FORWARD] },
                  name='rapoo-m50-sidebuttons', bustype=0x03)

def send_back(ui: UInput, pressed: bool):
    if MODE == 'altarrow':
        if pressed:
            ui.write(e.EV_KEY, e.KEY_LEFTALT, 1)
            ui.write(e.EV_KEY, e.KEY_LEFT, 1); ui.syn()
            ui.write(e.EV_KEY, e.KEY_LEFT, 0)
            ui.write(e.EV_KEY, e.KEY_LEFTALT, 0); ui.syn()
    else:
        ui.write(e.EV_KEY, e.KEY_BACK, 1 if pressed else 0); ui.syn()

def send_forward(ui: UInput, pressed: bool):
    if MODE == 'altarrow':
        if pressed:
            ui.write(e.EV_KEY, e.KEY_LEFTALT, 1)
            ui.write(e.EV_KEY, e.KEY_RIGHT, 1); ui.syn()
            ui.write(e.EV_KEY, e.KEY_RIGHT, 0)
            ui.write(e.EV_KEY, e.KEY_LEFTALT, 0); ui.syn()
    else:
        ui.write(e.EV_KEY, e.KEY_FORWARD, 1 if pressed else 0); ui.syn()

def main():
    cands = find_candidates()
    if not cands:
        print("No Rapoo 24AE:2015 hidraw nodes found.")
        sys.exit(1)

    print("Candidates:")
    for devnode, name, hidid in cands:
        print(f" - {devnode}  name='{name}'  HID_ID='{hidid}'")

    # open all candidates nonblocking
    fds = []
    for devnode, _, _ in cands:
        try:
            fd = os.open(devnode, os.O_RDONLY | os.O_NONBLOCK)
            flags = fcntl.fcntl(fd, fcntl.F_GETFD)
            fcntl.fcntl(fd, fcntl.F_SETFD, flags | fcntl.FD_CLOEXEC)
            fds.append((devnode, fd))
        except Exception as ex:
            print("Failed to open", devnode, ex)

    if not fds:
        print("Could not open any hidraw device.")
        sys.exit(1)

    print(f"\nMode: {MODE}  (set RAPOO_MODE=altarrow if needed)")
    ui = make_uinput()
    prev_back = prev_forward = 0

    while True:
        did_any = False
        for devnode, fd in list(fds):
            try:
                data = os.read(fd, 64)
                if not data: continue
            except BlockingIOError:
                continue
            except OSError:
                try: os.close(fd)
                except: pass
                fds.remove((devnode, fd))
                continue

            if len(data) >= 2 and data[0] == 0x01:
                mask = data[1]
                cur_back    = 1 if (mask & 0x10) else 0  # observed for one side button
                cur_forward = 1 if (mask & 0x08) else 0  # observed for the other
                if DEBUG:
                    print(f"{devnode} report: {data[:7].hex()} mask=0x{mask:02x}")

                if cur_back != prev_back:
                    send_back(ui, cur_back)
                    prev_back = cur_back
                if cur_forward != prev_forward:
                    send_forward(ui, cur_forward)
                    prev_forward = cur_forward
                did_any = True

        if not did_any:
            time.sleep(0.003)

if __name__ == '__main__':
    main()
