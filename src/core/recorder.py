import threading
import time
import os
import signal
import sys
from datetime import datetime

from src.core.capture import ScreenCapture
from src.core.audio import AudioCapture
from src.core.encoder import VideoEncoder
from src.core.crash_protection import CrashProtection
from src.core.history import RecordingHistory


class RecordingState:
    IDLE = "idle"
    RECORDING = "recording"
    PAUSED = "paused"


class RecorderManager:
    def __init__(self, config=None):
        self.config = config or {}
        self.state = RecordingState.IDLE
        self.screen_capture = None
        self.audio_capture = None
        self.video_encoder = None
        self.recording_thread = None
        self.is_running = False
        self.is_paused = False
        self.start_time = None
        self.elapsed_time = 0
        self.pause_time = 0
        self.callbacks = {
            "on_state_change": None,
            "on_frame": None,
            "on_timer": None,
            "on_file_size": None,
            "on_complete": None,
            "on_error": None
        }
        self.temp_frames = []
        self.frame_lock = threading.Lock()
        self.crash_protection = CrashProtection()
        self.history = RecordingHistory()
    
    def set_callback(self, name, callback):
        if name in self.callbacks:
            self.callbacks[name] = callback
    
    def _notify_state_change(self, state):
        self.state = state
        if self.callbacks["on_state_change"]:
            self.callbacks["on_state_change"](state)
    
    def start_recording(self):
        try:
            fps = self.config.get("fps", 30)
            format = self.config.get("format", "mp4")
            output_dir = self.config.get("output_dir")
            mic_volume = self.config.get("mic_volume", 80)
            sys_volume = self.config.get("sys_volume", 100)
            mic_enabled = self.config.get("mic_enabled", True)
            sys_audio_enabled = self.config.get("sys_audio_enabled", True)
            
            self.video_encoder = VideoEncoder(
                output_dir=output_dir,
                fps=fps,
                format=format
            )
            
            self.screen_capture = ScreenCapture(fps=fps)
            self.screen_capture.set_frame_callback(self._on_frame_captured)
            
            monitor_info = self.screen_capture.get_monitor_info()
            self.video_encoder.start_recording(
                monitor_info["width"],
                monitor_info["height"]
            )
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            audio_file = os.path.join(output_dir or os.path.join(os.path.expanduser("~"), "Videos", "LiteRecord"), f"audio_{timestamp}.wav")
            
            self.audio_capture = AudioCapture(
                mic_volume=mic_volume,
                sys_volume=sys_volume
            )
            self.audio_capture.mic_enabled = mic_enabled
            self.audio_capture.sys_audio_enabled = sys_audio_enabled
            self.audio_capture.set_audio_callback(self._on_audio_captured)
            
            self.is_running = True
            self.is_paused = False
            self.start_time = time.time()
            self.elapsed_time = 0
            
            self.screen_capture.start()
            self.audio_capture.start(audio_file_path=audio_file)
            
            self.crash_protection.enable(self)
            
            self._notify_state_change(RecordingState.RECORDING)
            
            self.timer_thread = threading.Thread(target=self._timer_loop, daemon=True)
            self.timer_thread.start()
            
            return True
        except Exception as e:
            self._notify_error(f"Failed to start recording: {str(e)}")
            return False
    
    def stop_recording(self):
        if not self.is_running:
            return None
        
        self.crash_protection.disable()
        
        self.is_running = False
        
        if self.screen_capture:
            self.screen_capture.stop()
        
        audio_file = self.audio_capture.audio_file_path if self.audio_capture else None
        
        if self.audio_capture:
            self.audio_capture.stop()
        
        result = None
        if self.video_encoder:
            result = self.video_encoder.stop_recording(
                audio_file_path=audio_file,
                on_merge_complete=self._on_merge_complete
            )
            
            fps = self.config.get("fps", 30)
            format = self.config.get("format", "mp4")
            self.history.add_recording(
                file_path=result["file"],
                duration=result["duration"],
                file_size=result["file_size"],
                fps=fps,
                format=format
            )
        
        self._notify_state_change(RecordingState.IDLE)
        
        if self.callbacks["on_complete"] and result:
            self.callbacks["on_complete"](result)
        
        return result
    
    def _on_merge_complete(self, final_file):
        if final_file and self.callbacks["on_complete"]:
            self.callbacks["on_complete"]({"file": final_file})
    
    def pause_recording(self):
        if self.is_running and not self.is_paused:
            self.is_paused = True
            self.pause_time = time.time()
            if self.screen_capture:
                self.screen_capture.stop()
            if self.audio_capture:
                self.audio_capture.stop()
            self._notify_state_change(RecordingState.PAUSED)
    
    def resume_recording(self):
        if self.is_running and self.is_paused:
            self.is_paused = False
            pause_duration = time.time() - self.pause_time
            self.start_time += pause_duration
            if self.screen_capture:
                self.screen_capture.start()
            if self.audio_capture:
                self.audio_capture.start()
            self._notify_state_change(RecordingState.RECORDING)
    
    def _on_frame_captured(self, frame):
        if self.is_running and not self.is_paused:
            self.video_encoder.write_frame(frame)
            if self.callbacks["on_frame"]:
                self.callbacks["on_frame"](frame)
    
    def _on_audio_captured(self, audio_data):
        pass
    
    def _timer_loop(self):
        while self.is_running:
            if not self.is_paused:
                self.elapsed_time = time.time() - self.start_time
                if self.callbacks["on_timer"]:
                    self.callbacks["on_timer"](self.elapsed_time)
                
                if self.callbacks["on_file_size"]:
                    size = self.video_encoder.get_file_size() if self.video_encoder else 0
                    self.callbacks["on_file_size"](size)
                
                self.crash_protection.heartbeat()
            
            time.sleep(0.5)
    
    def _notify_error(self, error_msg):
        if self.callbacks["on_error"]:
            self.callbacks["on_error"](error_msg)
    
    def get_elapsed_time(self):
        return self.elapsed_time
    
    def cleanup(self):
        if self.is_running:
            self.stop_recording()
        if self.audio_capture:
            self.audio_capture.cleanup()
