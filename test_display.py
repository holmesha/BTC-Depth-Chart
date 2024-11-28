#This file helps test your display before messing around with all the actual code

from PIL import Image, ImageDraw, ImageFont
from st7796 import ST7796
import time

# Initialize the display
display = ST7796(width=320, height=480, rotation=0, port=0, cs=0, dc=24, rst=25)

def display_test_image():
    # Create a blank image
    img = Image.new('RGB', (display.width, display.height), 'black')
    draw = ImageDraw.Draw(img)

    # Draw test shapes and text
    draw.rectangle((10, 10, 310, 470), outline="white", width=3)  # Rectangle border
    draw.line((10, 240, 310, 240), fill="red", width=2)  # Horizontal line
    draw.line((160, 10, 160, 470), fill="blue", width=2)  # Vertical line
    draw.text((20, 20), "Screen Test", fill="yellow")  # Text
    draw.ellipse((100, 180, 220, 300), outline="green", width=3)  # Circle

    # Display the image
    display.display(img)

def clear_screen():
    # Clear the screen
    img = Image.new('RGB', (display.width, display.height), 'black')
    display.display(img)

# Run the test
clear_screen()
display_test_image()

# Pause to observe
time.sleep(10)

# Clear the screen
clear_screen()


