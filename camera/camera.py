import machine
import camera
import time
import os

# --- Configuration Pins ---
PIR_PIN = 13  # Connected to PIR signal out

# --- Initialize Hardware ---
# Setup PIR sensor as an input pin with a pull-down resistor
pir = machine.Pin(PIR_PIN, machine.Pin.IN, machine.Pin.PULL_DOWN)

def mount_sd():
    """Mounts the MicroSD card to the /sd directory"""
    try:
        # AI-Thinker boards usually use the built-in slot via machine.SDCard()
        # slots: 1 (1-bit mode, uses fewer pins) or 3 (standard mode)
        # Slot 1 is highly stable on ESP32-CAM
        sd = machine.SDCard(slot=1)
        os.mount(sd, "/sd")
        print("SD Card mounted successfully at /sd")
        return True
    except Exception as e:
        print("Failed to mount SD card:", e)
        return False

def take_and_save_photo():
    """Initializes camera, captures a frame, saves to SD, and turns off camera"""
    print("Motion detected! Initializing camera...")

    # Initialize camera using your working configuration
    if not camera.init(0, format=camera.JPEG):
        print("Camera initialization failed.")
        return

    try:
        # Give sensor a moment to adjust to lighting conditions
        time.sleep(1.5)

        # Capture frame
        img = camera.capture()
        if img:
            # Generate a simple timestamp file name
            timestamp = int(time.time())
            filename = "/sd/motion_{}.jpg".format(timestamp)

            with open(filename, "wb") as f:
                f.write(img)
                print("Photo successfully saved to: {}".format(filename))
        else:
            print("Capture failed to grab a frame.")

    except Exception as e:
        print("Error during capture/save saving:", e)

    finally:
        # Always deinitialize to release pins and RAM
        camera.deinit()


# --- Main Logic Loop ---
if __name__ == '__main__':
    if mount_sd():
        print("System armed. Waiting for motion...")

        while True:
            if pir.value() == 1:
                take_and_save_photo()

                print("Cooldown period. Waiting for PIR to reset...")
                # Wait until the PIR output drops back to low before looking for next motion
                while pir.value() == 1:
                    time.sleep(0.5)
                print("System re-armed.")

            time.sleep(0.1)  # Small delay to keep the CPU cool
    else:
        print("System halted because SD card was not found.")
