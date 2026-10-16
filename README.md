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
poetry run mpremote cp securitycamera/webserver.py :webserver.py
poetry run mpremote repl  # you may need to reboot with ctrl+D
```

### Viewing photos over WiFi

The ESP32 starts its own WiFi access point, `ESP32_AP_Mode`, at boot. The SSID
and password are set in `connect_wifi()` in `securitycamera/main.py`.

1. Connect your phone or computer to `ESP32_AP_Mode` with the password from
   `connect_wifi()`.
2. Open `http://192.168.4.1/` in a browser.

#### When the web server runs

The web server only runs while at least one device is connected to the access
point:

- When a device connects, the main loop starts the web server on port 80 on its
  next pass, and the onboard LED on GPIO 33 lights up.
- When the last device disconnects, the server stops within about a second,
  releases port 80, and the LED turns off.
- While the server is running, the main loop is busy serving pages. **PIR motion
  is not checked and no photos are captured** until the last device disconnects.

#### The gallery page

- Lists every `.jpg` or `.jpeg` file in `/sd`, shown as a thumbnail with its
  filename. Refresh the page to see new captures.
- **Download** saves a copy of the photo.
- **Delete** removes one photo after a confirmation prompt.
- **Delete all** removes every photo listed on the page after a confirmation
  prompt.

#### HTTP routes

| Method | Path                       | Purpose                                  |
|--------|----------------------------|------------------------------------------|
| GET    | `/` or `/index.html`       | Gallery page                             |
| GET    | `/file?path=<filename>`    | Serves one photo                         |
| POST   | `/delete`                  | Deletes one photo (form field `path`)    |
| POST   | `/delete_all`              | Deletes every photo in `/sd`             |

Any other path returns `404 Page Not Found`.

#### Limitations

- Requests are handled one at a time.
- There is no login. Anyone who joins the access point can view and delete
  photos.
