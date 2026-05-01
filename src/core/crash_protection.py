import os
import sys
import signal
import threading
import time
import json
from datetime import datetime


class CrashProtection:
    def __init__(self, temp_dir=None):
        self.temp_dir = temp_dir or os.path.join(os.path.expanduser("~"), "Videos", "LiteRecord", ".temp")
        os.makedirs(self.temp_dir, exist_ok=True)
        self.is_active = False
        self.recorder_ref = None
        self.monitor_thread = None
        self.last_heartbeat = None
        self.check_interval = 5
        self.crash_log = []
    
    def enable(self, recorder):
        self.recorder_ref = recorder
        self.is_active = True
        self.last_heartbeat = time.time()
        self._save_session_state()
        
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        
        self._register_signal_handlers()
    
    def disable(self):
        self.is_active = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=2.0)
        self._clear_session_state()
    
    def heartbeat(self):
        if self.is_active:
            self.last_heartbeat = time.time()
            self._save_session_state()
    
    def _monitor_loop(self):
        while self.is_active:
            time.sleep(self.check_interval)
            if self.last_heartbeat:
                elapsed = time.time() - self.last_heartbeat
                if elapsed > 30:
                    self._handle_potential_crash()
    
    def _handle_potential_crash(self):
        session_file = os.path.join(self.temp_dir, "current_session.json")
        if os.path.exists(session_file):
            try:
                with open(session_file, 'r') as f:
                    session_data = json.load(f)
                
                temp_video = session_data.get("temp_video")
                if temp_video and os.path.exists(temp_video):
                    final_path = temp_video.replace(".temp.mp4", "_recovered.mp4")
                    if os.path.exists(temp_video):
                        os.rename(temp_video, final_path)
                        self._log_crash_recovery(final_path)
            except Exception as e:
                print(f"Crash recovery error: {e}")
    
    def _save_session_state(self):
        session_file = os.path.join(self.temp_dir, "current_session.json")
        try:
            session_data = {
                "start_time": datetime.now().isoformat(),
                "last_heartbeat": self.last_heartbeat,
                "pid": os.getpid(),
                "temp_video": self.recorder_ref.video_encoder.current_file if self.recorder_ref and self.recorder_ref.video_encoder else None,
                "state": self.recorder_ref.state if self.recorder_ref else "unknown"
            }
            with open(session_file, 'w') as f:
                json.dump(session_data, f, indent=2)
        except Exception as e:
            print(f"Failed to save session state: {e}")
    
    def _clear_session_state(self):
        session_file = os.path.join(self.temp_dir, "current_session.json")
        if os.path.exists(session_file):
            try:
                os.remove(session_file)
            except:
                pass
    
    def _register_signal_handlers(self):
        def signal_handler(signum, frame):
            self._handle_unexpected_exit()
            sys.exit(1)
        
        signal.signal(signal.SIGTERM, signal_handler)
        signal.signal(signal.SIGINT, signal_handler)
    
    def _handle_unexpected_exit(self):
        if self.recorder_ref and self.recorder_ref.is_running:
            self.recorder_ref.stop_recording()
    
    def _log_crash_recovery(self, recovered_file):
        log_entry = {
            "time": datetime.now().isoformat(),
            "recovered_file": recovered_file,
            "action": "crash_recovery"
        }
        self.crash_log.append(log_entry)
        
        recovery_log = os.path.join(self.temp_dir, "recovery_log.json")
        try:
            with open(recovery_log, 'w') as f:
                json.dump(self.crash_log, f, indent=2)
        except:
            pass
    
    def get_recovery_files(self):
        recovery_files = []
        if os.path.exists(self.temp_dir):
            for file in os.listdir(self.temp_dir):
                if file.endswith("_recovered.mp4"):
                    full_path = os.path.join(self.temp_dir, file)
                    recovery_files.append({
                        "path": full_path,
                        "size": os.path.getsize(full_path),
                        "modified": datetime.fromtimestamp(os.path.getmtime(full_path)).isoformat()
                    })
        return recovery_files
