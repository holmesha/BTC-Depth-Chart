#!/usr/bin/env python3

import time
import threading
import websocket
import json
from PIL import Image, ImageDraw, ImageFont
from st7796 import ST7796

# Initialize the display with horizontal layout
display = ST7796(
    width=480,  # Horizontal width
    height=320,  # Horizontal height
    rotation=270,  # Rotate 90 degrees for landscape mode
    port=0,
    cs=0,
    dc=24,
    rst=25
)

# Global order book variables
bids = {}
asks = {}
current_price = 0  # To store the mid-price for display

# Variables for rate limiting chart updates
last_update_time = 0
update_interval = 1  # Update chart every 1 second

def on_message(ws, message):
    """Handle incoming WebSocket messages."""
    global bids, asks, current_price
    data = json.loads(message)
    if isinstance(data, dict):
        if data.get("event") == "subscriptionStatus":
            print("Subscription acknowledged:", data)
        elif data.get("event") == "heartbeat":
            print("Heartbeat received")
    elif isinstance(data, list):
        if "as" in data[1] or "bs" in data[1]:  # Snapshot
            update_order_book_snapshot(data[1])
        elif "a" in data[1] or "b" in data[1]:  # Updates
            update_order_book(data[1])

        # Update the current price immediately
        if bids and asks:
            best_bid = max(bids.keys())
            best_ask = min(asks.keys())
            current_price = (best_bid + best_ask) / 2

        # Trigger a chart update after processing the message
        update_chart()
    else:
        print("Unknown message format:", data)

def on_error(ws, error):
    print("WebSocket error:", error)

def on_close(ws, close_status_code, close_msg):
    print("WebSocket connection closed. Attempting to reconnect...")
    time.sleep(5)
    start_websocket()

def on_open(ws):
    """Subscribe to the Kraken order book."""
    print("WebSocket connection opened")
    subscribe_message = {
        "event": "subscribe",
        "pair": ["XBT/USD"],
        "subscription": {"name": "book", "depth": 25}
    }
    ws.send(json.dumps(subscribe_message))

def start_websocket():
    """Start the Kraken WebSocket connection."""
    websocket.enableTrace(False)
    ws = websocket.WebSocketApp(
        "wss://ws.kraken.com/",
        on_open=on_open,
        on_message=on_message,
        on_error=on_error,
        on_close=on_close
    )
    ws.run_forever()

def update_order_book_snapshot(data):
    """Initialize the order book with a snapshot."""
    global bids, asks
    if "as" in data:
        asks = {float(price): float(volume) for price, volume, _ in data["as"]}
    if "bs" in data:
        bids = {float(price): float(volume) for price, volume, _ in data["bs"]}

def update_order_book(data):
    """Update the order book with incremental updates."""
    global bids, asks
    if "a" in data:
        for update in data["a"]:
            price = float(update[0])
            volume = float(update[1]) if update[1] else 0.0
            if volume == 0.0:
                asks.pop(price, None)
            else:
                asks[price] = volume
    if "b" in data:
        for update in data["b"]:
            price = float(update[0])
            volume = float(update[1]) if update[1] else 0.0
            if volume == 0.0:
                bids.pop(price, None)
            else:
                bids[price] = volume

def update_chart():
    """Render and display the depth chart."""
    global bids, asks, current_price

    # Sort and process order book data
    sorted_bids = sorted(bids.items(), key=lambda x: x[0], reverse=True)[:20]
    sorted_asks = sorted(asks.items(), key=lambda x: x[0])[:20]

    # Calculate cumulative volumes
    cum_bids = []
    cum_asks = []
    total_bid_volume = 0
    total_ask_volume = 0

    for price, volume in sorted_bids:
        total_bid_volume += volume
        cum_bids.append((price, total_bid_volume))

    for price, volume in sorted_asks:
        total_ask_volume += volume
        cum_asks.append((price, total_ask_volume))

    # Calculate net volume trend
    net_volume = total_bid_volume - total_ask_volume

    # Create an image for the chart
    img = Image.new("RGB", (display.width, display.height), "black")
    draw = ImageDraw.Draw(img)

    # Define chart area
    left_padding = 5
    label_area_width = 40
    chart_x = left_padding
    chart_y = 40
    chart_width = display.width - left_padding - label_area_width
    chart_height = display.height - chart_y - 20

    # Determine price ranges
    min_price = min([price for price, _ in cum_bids], default=0)
    max_price = max([price for price, _ in cum_asks], default=1)
    max_volume_bids = max(total_bid_volume, 1)  # Avoid division by zero
    max_volume_asks = max(total_ask_volume, 1)

    # Ensure the current price is centered
    min_price = min(min_price, current_price)
    max_price = max(max_price, current_price)

    # Scaling factors
    price_scale = chart_width / (max_price - min_price) if (max_price - min_price) != 0 else 1
    bid_volume_scale = chart_height / max_volume_bids
    ask_volume_scale = chart_height / max_volume_asks

    # Draw the net volume trend arrow
    arrow_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 24)
    if net_volume > 0:
        arrow = "↑"
        arrow_color = "green"
    elif net_volume < 0:
        arrow = "↓"
        arrow_color = "red"
    else:
        arrow = "-"  # No significant trend
        arrow_color = "white"

    # Position the arrow near the top-right corner of the chart
    arrow_x = chart_x + chart_width - 100  # Adjusted for better placement
    arrow_y = 10
    draw.text((arrow_x, arrow_y), arrow, fill=arrow_color, font=arrow_font)

    # Draw axes
    draw.line((chart_x, chart_y + chart_height, chart_x + chart_width, chart_y + chart_height), fill="white")  # X-axis
    draw.line((chart_x, chart_y, chart_x, chart_y + chart_height), fill="white")  # Y-axis

    # Plot bids (green)
    last_x = chart_x
    last_y = chart_y + chart_height
    for price, volume in cum_bids:
        x = chart_x + int((price - min_price) * price_scale)
        y = chart_y + chart_height - int(volume * bid_volume_scale)  # Scale bids independently
        draw.rectangle((last_x, y, x, chart_y + chart_height), fill="green")
        draw.line((last_x, last_y, x, y), fill="darkgreen")
        last_x, last_y = x, y

    # Plot asks (red)
    last_x = chart_x + int((current_price - min_price) * price_scale)
    last_y = chart_y + chart_height
    for price, volume in cum_asks:
        x = chart_x + int((price - min_price) * price_scale)
        y = chart_y + chart_height - int(volume * ask_volume_scale)  # Scale asks independently
        draw.rectangle((last_x, y, x, chart_y + chart_height), fill="red")
        draw.line((last_x, last_y, x, y), fill="darkred")
        last_x, last_y = x, y

    # Draw vertical white line for current price
    if current_price:
        x = chart_x + int((current_price - min_price) * price_scale)
        draw.line((x, chart_y, x, chart_y + chart_height), fill="white", width=2)

        # Reposition the small white price label
        font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 12)
        label_x = x + 10  # Slightly to the right of the line
        label_y = chart_y + chart_height - 20  # Slightly down from the line
        draw.text((label_x, label_y), f"${current_price:.2f}", fill="white", font=font_small)

    # Draw price labels on the right
    font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 12)
    num_labels = 5
    for i in range(num_labels + 1):
        price = min_price + (i / num_labels) * (max_price - min_price)
        y = chart_y + chart_height - int(i / num_labels * chart_height)
        label = f"${price:.2f}"
        label_x = display.width - label_area_width - 35
        draw.text((label_x, y - 8), label, fill="white", font=font_small)

    # Load fonts
    font_large = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 24)

    # Add the name of the security at the top with the current price
    btc_label = "BTC"
    price_label = f"${current_price:.2f}"
    draw.text((chart_x + 10, 10), btc_label, fill="white", font=font_large)
    draw.text((chart_x + 80, 10), price_label, fill="orange", font=font_large)

    # Display the chart
    display.display(img)

if __name__ == "__main__":
    ws_thread = threading.Thread(target=start_websocket)
    ws_thread.daemon = True
    ws_thread.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Program terminated")
        display.cleanup()
