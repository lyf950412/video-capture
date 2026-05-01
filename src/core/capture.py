import mss
import mss.tools
import numpy as np
from PIL import Image
import threading
import time


class ScreenCapture:
    def __init__(self, region=None, fps=30):
        self.region = region
        self.fps = fps
        self.sct = None
        self.monitor = None
        self.running = False
        self.frame_callback = None
        self.capture_thread = None
        
        with mss.mss() as sct:
            if region is None:
                self.monitor = sct.monitors[1]
            else:
                self.monitor = {
                    "top": region[1],
                    "left": region[0],
                    "width": region[2],
                    "height": region[3]
                }
    
    def set_frame_callback(self, callback):
        self.frame_callback = callback
    
    def start(self):
        self.running = True
        self.capture_thread = threading.Thread(target=self._capture_loop, daemon=True)
        self.capture_thread.start()
    
    def stop(self):
        self.running = False
        if self.capture_thread:
            self.capture_thread.join(timeout=2.0)
    
    def _capture_loop(self):
        with mss.mss() as sct:
            interval = 1.0 / self.fps
            last_time = time.time()
            
            while self.running:
                try:
                    frame = sct.grab(self.monitor)
                    frame_array = np.array(frame)
                    frame_array = frame_array[:, :, :3]
                    
                    if self.frame_callback:
                        self.frame_callback(frame_array)
                    
                    elapsed = time.time() - last_time
                    sleep_time = interval - elapsed
                    if sleep_time > 0:
                        time.sleep(sleep_time)
                    last_time = time.time()
                except Exception as e:
                    print(f"Screen capture error: {e}")
                    time.sleep(0.01)
    
    def get_monitor_info(self):
        return {
            "width": self.monitor["width"],
            "height": self.monitor["height"],
            "top": self.monitor["top"],
            "left": self.monitor["left"]
        }
