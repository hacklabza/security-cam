import machine
import camera
import time
import os


PIR_PIN = 13  # Connected to PIR signal out
FLASH_PIN = 4  # Connected to the camera flash control pin

pir = machine.Pin(PIR_PIN, machine.Pin.IN, machine.Pin.PULL_DOWN)
flash = machine.Pin(FLASH_PIN, machine.Pin.OUT)

def mount_sd():
    """Mounts the MicroSD card to the /sd directory"""
    try:
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
        # Turn on the flash
        flash.on()

        # Give sensor a moment to adjust to lighting conditions
        time.sleep(1.5)

        # Capture frame
        img = camera.capture()
        if img:
            # Generate a simple timestamp file name
            timestamp = int(time.time())
            filename = f"/sd/motion_{timestamp}.jpg"

            with open(filename, "wb") as _file:
                _file.write(img)
                print(f"Photo successfully saved to: {filename}")
        else:
            print("Capture failed to grab a frame.")

            # Turn off the flash after capturing the photo
            flash.off()

    except Exception as e:
        print("Error during capture/save saving:", e)

    finally:
        # Always deinitialize to release pins and RAM
        camera.deinit()

        # Ensure the flash is turned off
        flash.off()


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
                    machine.lightsleep(500)
                print("System re-armed.")

            machine.lightsleep(500)
    else:
        print("System halted because SD card was not found.")
