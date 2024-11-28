import spidev
import RPi.GPIO as GPIO
import time
from PIL import Image

class ST7796:
    def __init__(self, width=320, height=480, rotation=270, port=0, cs=0, dc=24, rst=25, backlight=None):
        self.width = width
        self.height = height
        self.rotation = rotation

        # Initialize SPI
        self.spi = spidev.SpiDev(port, cs)
        self.spi.max_speed_hz = 40000000  # SPI speed: 40 MHz
        self.spi.mode = 0

        # GPIO pins
        self.dc = dc
        self.rst = rst
        self.backlight = backlight

        # Setup GPIO
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.dc, GPIO.OUT)
        GPIO.setup(self.rst, GPIO.OUT)
        GPIO.setwarnings(False)  # Suppress warnings
        GPIO.setmode(GPIO.BCM)   # Use BCM GPIO numbering
        if self.backlight is not None:
            GPIO.setup(self.backlight, GPIO.OUT)

        # Initialize the display
        self.reset()
        self.init_display()

    def reset(self):
        """Reset the display."""
        GPIO.output(self.rst, GPIO.HIGH)
        time.sleep(0.1)
        GPIO.output(self.rst, GPIO.LOW)
        time.sleep(0.1)
        GPIO.output(self.rst, GPIO.HIGH)
        time.sleep(0.2)

    def command(self, cmd, data=None):
        """Send a command to the display."""
        GPIO.output(self.dc, GPIO.LOW)
        self.spi.writebytes([cmd])
        if data is not None:
            self.data(data)

    def data(self, data):
        """Send data to the display."""
        GPIO.output(self.dc, GPIO.HIGH)
        if isinstance(data, list):
            self.spi.writebytes(data)
        else:
            self.spi.writebytes([data])

    def init_display(self):
        """Initialize the display with the ST7796 initialization sequence."""
        # Power control
        self.command(0x11)  # Sleep out
        time.sleep(0.12)

        # Memory data access control
        self.command(0x36, [0x48])  # Row/column exchange, RGB order

        # Interface pixel format
        self.command(0x3A, [0x55])  # 16 bits/pixel (RGB565)

        # Porch setting
        self.command(0xB2, [0x0C, 0x0C, 0x00, 0x33, 0x33])

        # Display function control
        self.command(0xB7, [0x35])  # Gate and source output directions

        # Power control
        self.command(0xBB, [0x19])  # VCOM setting
        self.command(0xC0, [0x2C])  # Power control 1
        self.command(0xC2, [0x01])  # Power control 2
        self.command(0xC3, [0x12])  # Power control 3
        self.command(0xC4, [0x20])  # Power control 4
        self.command(0xC6, [0x0F])  # Frame rate control

        # Gamma correction
        self.command(0xE0, [0xD0, 0x08, 0x11, 0x08, 0x0C, 0x15, 0x39, 0x33, 0x50, 0x36, 0x13, 0x14, 0x29, 0x2D])
        self.command(0xE1, [0xD0, 0x08, 0x10, 0x08, 0x06, 0x06, 0x39, 0x44, 0x51, 0x0B, 0x16, 0x14, 0x2F, 0x31])

        # Turn on the display
        self.command(0x29)  # Display ON
        time.sleep(0.12)

    def display(self, image):
        """Display an image on the screen."""
        # Rotate the image as needed
        if self.rotation == 90:
            image = image.rotate(90, expand=True)
        elif self.rotation == 180:
            image = image.rotate(180, expand=True)
        elif self.rotation == 270:
            image = image.rotate(270, expand=True)

        # Convert the image to RGB565 format
        pixel_bytes = self.image_to_data(image)

        # Set column and row addresses
        self.command(0x2A, [0x00, 0x00, 0x01, 0x3F])  # Column address
        self.command(0x2B, [0x00, 0x00, 0x01, 0xDF])  # Row address
        self.command(0x2C)  # Write to RAM

        # Send the pixel data in chunks of 4096 bytes
        GPIO.output(self.dc, GPIO.HIGH)
        for i in range(0, len(pixel_bytes), 4096):
            self.spi.writebytes(pixel_bytes[i:i + 4096])


    def image_to_data(self, image):
        """Convert an image to 16-bit 565 RGB bytes."""
        image = image.convert("RGB")
        pixels = list(image.getdata())
        data = []
        for r, g, b in pixels:
            rgb565 = ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)
            data.append((rgb565 >> 8) & 0xFF)  # High byte
            data.append(rgb565 & 0xFF)  # Low byte
        return data

    def cleanup(self):
        """Clean up GPIO and SPI resources."""
        GPIO.output(self.dc, GPIO.LOW)
        if self.backlight is not None:
            GPIO.output(self.backlight, GPIO.LOW)
        self.spi.close()
        GPIO.cleanup()
