import gi
gi.require_version('Gst', '1.0')
from gi.repository import Gst, GLib
import numpy as np

class VideoReceiver:
    def __init__(self, callback):
        self.pipeline = None
        self.callback = callback # Function to call with decoded frames
        self.loop = GLib.MainLoop()
        
    def start_receiving(self, port):
        """Starts listening for video stream on the specified port using GStreamer"""
        print(f"Starting video receiver on port {port}")
        
        # Pipeline: TCP Server -> H.264 Parse -> H.264 Decode -> Video Convert -> AppSink
        # tcpserversrc: listens for incoming TCP connections
        # h264parse: parses the H.264 stream
        # avdec_h264: decodes H.264 to raw video (software decoding)
        # videoconvert: ensures format compatibility (e.g., converts to BGR/RGB for OpenCV)
        # appsink: sends buffers to the application
        
        pipeline_str = (
            f"tcpserversrc port={port} ! "
            "h264parse ! "
            "avdec_h264 ! "
            "videoconvert ! "
            "video/x-raw,format=BGR ! "
            "appsink name=sink emit-signals=True sync=False"
        )
        
        try:
            # Launch the pipeline
            self.pipeline = Gst.parse_launch(pipeline_str)
            
            # Get the sink element to connect signal
            sink = self.pipeline.get_by_name("sink")
            if not sink:
                print("Error: Could not find appsink in pipeline")
                return

            sink.connect("new-sample", self._on_new_sample)
            
            # Start the pipeline
            ret = self.pipeline.set_state(Gst.State.PLAYING)
            if ret == Gst.StateChangeReturn.FAILURE:
                print("Error: Unable to set the pipeline to the playing state.")
                return
            
        except Exception as e:
            print(f"Error creating pipeline: {e}")

    def stop_receiving(self):
        print("Stopping video receiver")
        if self.pipeline:
            self.pipeline.set_state(Gst.State.NULL)
            self.pipeline = None

    def _on_new_sample(self, sink):
        """Callback for appsink when a new frame is available"""
        sample = sink.emit("pull-sample")
        if not sample:
            return Gst.FlowReturn.ERROR

        buffer = sample.get_buffer()
        caps = sample.get_caps()
        
        # Extract width and height from caps
        structure = caps.get_structure(0)
        width = structure.get_value("width")
        height = structure.get_value("height")
        
        # Map buffer to get data
        success, map_info = buffer.map(Gst.MapFlags.READ)
        if not success:
            return Gst.FlowReturn.ERROR
            
        try:
            # Create numpy array from data
            # BGR format (3 channels)
            frame = np.ndarray(
                shape=(height, width, 3),
                dtype=np.uint8,
                buffer=map_info.data
            )
            
            # Call the user callback with the frame
            if self.callback:
                self.callback(frame)
                
        except Exception as e:
            print(f"Error processing frame: {e}")
        finally:
            buffer.unmap(map_info)
            
        return Gst.FlowReturn.OK

