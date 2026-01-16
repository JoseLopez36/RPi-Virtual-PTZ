"""
Video Streamer Module

This module streams annotated video to a PC using GStreamer
"""

import gi
import threading
from typing import Optional

gi.require_version('Gst', '1.0')
from gi.repository import Gst, GLib

class VideoStreamer:
    def __init__(self):
        try:
            Gst.init(None)
            self.pipeline = None
            self.loop: Optional[GLib.MainLoop] = None
            self.loop_thread: Optional[threading.Thread] = None
            self.appsrc = None

            self._width: Optional[int] = None
            self._height: Optional[int] = None
            self._fps: Optional[int] = None
            self._frame_duration_ns: Optional[int] = None
            self._frame_count: int = 0
            print("GStreamer initialized")
        except Exception as e:
            print(f"Error initializing GStreamer: {e}")

    def start_stream(self, host, port, width, height, fps=30):
        """
        Starts streaming provided BGR frames as H.264 inside MPEG-TS via UDP.

        Frames must be pushed via `push_frame(frame_bgr)` after starting.
        """
        if self.pipeline:
            print("Stream already running")
            return

        try:
            self._width = int(width)
            self._height = int(height)
            self._fps = int(fps)
            if self._fps <= 0:
                raise ValueError(f"fps must be > 0, got {fps}")

            self._frame_duration_ns = int(Gst.SECOND // self._fps)
            self._frame_count = 0

            # Pipeline description:
            # appsrc: Python provides raw frames (BGR)
            # videoconvert: colorspace conversion
            # x264enc: software H.264 encoding (tuned for low latency)
            # h264parse: parses the H.264 stream
            # mpegtsmux: muxes into MPEG-TS
            # udpsink: sends via UDP
            pipeline_str = (
                f"appsrc name=src is-live=true do-timestamp=true format=time "
                f"caps=video/x-raw,format=BGR,width={self._width},height={self._height},framerate={self._fps}/1 ! "
                "queue leaky=downstream max-size-buffers=2 ! "
                "videoconvert ! video/x-raw,format=I420 ! "
                f"x264enc tune=zerolatency speed-preset=ultrafast key-int-max={self._fps} "
                "threads=0 ! "
                "h264parse config-interval=1 ! "
                "mpegtsmux ! "
                f"udpsink host={host} port={port} sync=false async=false"
            )
            
            print(f"Starting pipeline: {pipeline_str}")
            self.pipeline = Gst.parse_launch(pipeline_str)

            self.appsrc = self.pipeline.get_by_name("src")
            if self.appsrc is None:
                raise RuntimeError("Failed to acquire appsrc element (name=src)")
            try:
                # Avoid blocking the caller if downstream can't keep up.
                self.appsrc.set_property("block", False)
            except Exception:
                pass
            
            # Bus handling for error messages
            bus = self.pipeline.get_bus()
            bus.add_signal_watch()
            bus.connect("message", self._on_bus_message)
            
            # Start the pipeline
            ret = self.pipeline.set_state(Gst.State.PLAYING)
            if ret == Gst.StateChangeReturn.FAILURE:
                raise RuntimeError("Unable to set the pipeline to the playing state")
            
            # Start MainLoop in a separate thread to handle GStreamer messages
            self.loop = GLib.MainLoop()
            self.loop_thread = threading.Thread(target=self.loop.run)
            self.loop_thread.daemon = True
            self.loop_thread.start()
            
            print(f"Streaming to {host}:{port} started")
            
        except Exception as e:
            print(f"Failed to start stream: {e}")
            self.stop_stream()

    def push_frame(self, frame_bgr):
        """
        Push a single BGR frame (numpy array) into the GStreamer pipeline.

        Expected shape: (H, W, 3), dtype=uint8.
        """
        if self.pipeline is None or self.appsrc is None:
            raise RuntimeError("Stream not started; call start_stream() first")

        if frame_bgr is None:
            return

        try:
            h, w = frame_bgr.shape[:2]
        except Exception as e:
            raise ValueError(f"Invalid frame (no shape): {e}")

        if self._width is not None and self._height is not None:
            if int(w) != int(self._width) or int(h) != int(self._height):
                raise ValueError(
                    f"Frame size {w}x{h} does not match pipeline caps {self._width}x{self._height}"
                )

        data = frame_bgr.tobytes()
        buf = Gst.Buffer.new_allocate(None, len(data), None)
        buf.fill(0, data)

        if self._frame_duration_ns is not None:
            pts = int(self._frame_count * self._frame_duration_ns)
            buf.pts = pts
            buf.dts = pts
            buf.duration = int(self._frame_duration_ns)
            self._frame_count += 1

        ret = self.appsrc.emit("push-buffer", buf)
        if ret != Gst.FlowReturn.OK:
            raise RuntimeError(f"Failed to push buffer: {ret}")

    def stop_stream(self):
        """Stops the GStreamer pipeline"""
        if self.pipeline:
            try:
                if self.appsrc is not None:
                    try:
                        self.appsrc.emit("end-of-stream")
                    except Exception:
                        pass
                self.pipeline.set_state(Gst.State.NULL)
                print("Pipeline stopped")
            except Exception as e:
                print(f"Error stopping pipeline: {e}")
            self.pipeline = None
            self.appsrc = None

        if self.loop is not None and self.loop.is_running():
            try:
                self.loop.quit()
            except Exception:
                pass

        if self.loop_thread is not None and self.loop_thread.is_alive():
            try:
                self.loop_thread.join(timeout=1.0)
            except Exception:
                pass
        self.loop_thread = None
        self.loop = None

    def _on_bus_message(self, bus, message):
        t = message.type
        if t == Gst.MessageType.EOS:
            print("End-of-stream")
            self.stop_stream()
        elif t == Gst.MessageType.ERROR:
            err, debug = message.parse_error()
            print(f"GStreamer Error: {err}, {debug}")
            self.stop_stream()