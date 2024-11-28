# Raspberry Pi Depth Chart Project

A real-time **cryptocurrency depth chart** display for the Raspberry Pi Zero 2 W, powered by a 3.5-inch TFT touchscreen. This project uses data from Kraken's WebSocket API to visualize live bid/ask order book trends, including moving price markers and market volume trends.

## Features
- Real-time visualization of bid/ask order book data.
- Dynamic price line with a moving label.
- Green/Red arrow indicating market order volume trends.
- Clean, minimalist design optimized for a 480x320 TFT screen.

---

## Hardware Requirements
- **Raspberry Pi Zero 2 W**
- **3.5-inch TFT Touchscreen** (with ST7796 driver) - I used [the 3.5" screen from Aliexpress](https://www.aliexpress.us/item/3256805988905985.html?spm=a2g0o.order_list.order_list_main.40.14a91802hqBs01&gatewayAdapt=glo2usa).
- Power supply and connectivity setup for the Pi
- Optional 3D Printed Case (work in progress - case needs to be modified to fit the particular screen I used) [HERE](https://www.printables.com/model/677296-pi-zerozero2-35-inch-touch-screen-display-case/files)

---

## Software Requirements
- **Python 3.x**
- Libraries:
  - `Pillow`
  - `websocket-client`
  - `RPi.GPIO`
  - `spidev`

Install dependencies:
```bash
pip install pillow websocket-client RPi.GPIO spidev
```

## How to Run
- Clone this repository
```bash
git clone https://github.com/username/rpi-depth-chart.git
cd rpi-depth-chart
```

- Run this script
```bash
python3 real_time_depth_chart.py
```

## Optional - Make the File Executable
- Run the following command to give the script execution permissions:
```bash
chmod +x /path/to/real_time_depth_chart.py
```

- Edit the crontab file - select your editor of choice
```bash
crontab -e
```

- If you want this file to run at reboot automatically
```bash
@reboot /path/to/your_script.sh
```
