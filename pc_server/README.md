# PC Server Code

This directory contains the code to run on the Host PC (tested on Ubuntu 24.04).

## Responsibilities
1. Receive GStreamer video stream.
2. Decode video.
3. Run Deep Learning inference.
4. Publish control signals via MQTT.

## Setup
### 1. **System Dependencies (Ubuntu/Debian):**
   ```bash
   sudo apt-get update
   sudo apt-get install -y python3-gi python3-gi-cairo gir1.2-gtk-3.0 libgirepository1.0-dev libcairo2-dev
   sudo apt-get install libgstreamer1.0-dev \
      libgstreamer-plugins-base1.0-dev \
      libgstreamer-plugins-bad1.0-dev \
      gstreamer1.0-plugins-good \
      gstreamer1.0-plugins-ugly \
      gstreamer1.0-plugins-bad \
      gstreamer1.0-tools \
      gstreamer1.0-gl \
      gstreamer1.0-gtk3 \
      gstreamer1.0-libav \
      gstreamer1.0-vaapi
  ```

### 2. **Clone the Repository**
   ```bash
   git clone https://github.com/JoseLopez36/RPi-Edge-vs-Local.git
   cd RPi-Edge-vs-Local/pc_server
   ```

### 3. **Python Dependencies:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

## Run
1. Edit `scripts/main.py` to set the correct `MQTT_BROKER` IP.
2. Run the application:
   ```bash
   python3 scripts/main.py
   ```