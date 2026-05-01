import os
import json
import shutil
from datetime import datetime
from pathlib import Path


class RecordingHistory:
    def __init__(self, history_file=None):
        if history_file is None:
            history_dir = os.path.join(os.path.expanduser("~"), "Videos", "LiteRecord")
            os.makedirs(history_dir, exist_ok=True)
            history_file = os.path.join(history_dir, "history.json")
        
        self.history_file = history_file
        self.recordings = []
        self._load_history()
    
    def _load_history(self):
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    self.recordings = json.load(f)
            except:
                self.recordings = []
    
    def _save_history(self):
        try:
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(self.recordings, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Failed to save history: {e}")
    
    def add_recording(self, file_path, duration, file_size, fps=30, format="mp4"):
        if not os.path.exists(file_path):
            return None
        
        file_stat = os.stat(file_path)
        recording = {
            "id": datetime.now().strftime("%Y%m%d%H%M%S"),
            "file_path": file_path,
            "file_name": os.path.basename(file_path),
            "duration": duration,
            "file_size": file_size,
            "file_size_mb": file_size / (1024 * 1024),
            "fps": fps,
            "format": format,
            "created_at": datetime.fromtimestamp(file_stat.st_ctime).isoformat(),
            "modified_at": datetime.fromtimestamp(file_stat.st_mtime).isoformat(),
            "thumbnail": None,
            "tags": [],
            "notes": ""
        }
        
        self.recordings.insert(0, recording)
        self._save_history()
        
        return recording
    
    def get_recordings(self, limit=50, offset=0):
        return self.recordings[offset:offset + limit]
    
    def get_recording_by_id(self, recording_id):
        for recording in self.recordings:
            if recording["id"] == recording_id:
                return recording
        return None
    
    def delete_recording(self, recording_id):
        recording = self.get_recording_by_id(recording_id)
        if recording:
            file_path = recording["file_path"]
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except:
                    pass
            
            self.recordings.remove(recording)
            self._save_history()
            return True
        return False
    
    def search_recordings(self, query):
        results = []
        query_lower = query.lower()
        for recording in self.recordings:
            if (query_lower in recording["file_name"].lower() or
                query_lower in recording.get("tags", []) or
                query_lower in recording.get("notes", "")):
                results.append(recording)
        return results
    
    def get_statistics(self):
        if not self.recordings:
            return {
                "total_recordings": 0,
                "total_size_mb": 0,
                "total_duration_seconds": 0,
                "average_duration_seconds": 0
            }
        
        total_size = sum(r.get("file_size", 0) for r in self.recordings)
        total_duration = sum(r.get("duration", 0) for r in self.recordings)
        
        return {
            "total_recordings": len(self.recordings),
            "total_size_mb": total_size / (1024 * 1024),
            "total_duration_seconds": total_duration,
            "total_duration_hours": total_duration / 3600,
            "average_duration_seconds": total_duration / len(self.recordings) if self.recordings else 0
        }
    
    def cleanup_missing_files(self):
        removed = []
        for recording in self.recordings[:]:
            if not os.path.exists(recording["file_path"]):
                self.recordings.remove(recording)
                removed.append(recording["file_name"])
        
        if removed:
            self._save_history()
        
        return removed
