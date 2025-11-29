# Raspberry Pi Edge Code

This directory contains the code to run on the Raspberry Pi 4B.

## Responsibilities
1. Capture video from Pi Camera.
2. Encode video to H.264 using GStreamer.
3. Stream video to PC.
4. Listen for MQTT control signals.
5. Execute hardware actions (GPIO).

## Setup
### 1. **System Dependencies:**
   ```bash
   sudo apt-get update
   sudo apt-get install libx264-dev libjpeg-dev
   sudo apt-get install libgstreamer1.0-dev \
     libgstreamer-plugins-base1.0-dev \
     libgstreamer-plugins-bad1.0-dev \
     gstreamer1.0-plugins-good \
     gstreamer1.0-plugins-ugly \
     gstreamer1.0-plugins-bad \
     gstreamer1.0-tools \
     gstreamer1.0-libcamera \
     gstreamer1.0-gl \
     gstreamer1.0-gtk3
   ```

### 2. **Clone the Repository**
   ```bash
   git clone https://github.com/JoseLopez36/RPi-Edge-vs-Local.git
   cd RPi-Edge-vs-Local/rpi_edge
   ```

### 3. **Python Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

## Run
1. Make sure the PC Server is running first and you know its IP address.
2. Edit `scripts/main.py` to set the correct `PC_HOST` IP address and `MQTT_BROKER` IP.
3. Run the application:
   ```bash
   python3 scripts/main.py
   ```