# ESP32 PIR Security Camera

Simple PIR triggered security camera based on the ESP-cam module

## Requirements

- esptool
- screen (macOS)
- mpremote
- poetry
- micropython bin from https://github.com/lemariva/micropython-camera-driver

### Installation

Device installation requirements

```bash
# Install the python deps
poetry install

# Erase flash
poetry run esptool --port <device-port> --baud 115200 erase-flash

# Flash the chip
poetry run esptool --port <device-port> --baud 115200 write-flash --flash_freq 40m -z 0x1000 --bin-file ~/Downloads/micropython_camera_*.bin

# Check that you can repl onto the board
poetry run mpremote repl

# Install the camera firmware
poetry run mpremote cp securitycamera/main.py :main.py
poetry run mpremote repl  # you may need to reboot with ctrl+X
```
