import cv2
import numpy as np
import os
import time
import threading
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class VideoEncoder:
    def __init__(self, output_dir=None, fps=30, format="mp4"):
        self.fps = fps
        self.format = format
        self.output_dir = output_dir or os.path.join(os.path.expanduser("~"), "Videos", "CapSure")
        self.writer = None
        self.current_file = None
        self.frame_count = 0
        self.start_time = None
        self.is_writing = False
        self.file_size = 0
        self.lock = threading.Lock()
        
        os.makedirs(self.output_dir, exist_ok=True)
    
    def start_recording(self, width, height):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.current_file = os.path.join(self.output_dir, f"recording_{timestamp}.{self.format}")
        
        if self.format == "mp4":
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        elif self.format == "mkv":
            fourcc = cv2.VideoWriter_fourcc(*'XVID')
        else:
            fourcc = cv2.VideoWriter_fourcc(*'vp80')
        
        self.writer = cv2.VideoWriter(
            self.current_file,
            fourcc,
            self.fps,
            (width, height)
        )
        
        if not self.writer.isOpened():
            raise Exception(f"Failed to create video file: {self.current_file}")
        
        self.is_writing = True
        self.frame_count = 0
        self.start_time = time.time()
        self.file_size = 0
        
        return self.current_file
    
    def write_frame(self, frame):
        if self.writer and self.is_writing:
            with self.lock:
                self.writer.write(frame)
                self.frame_count += 1
                self.file_size = os.path.getsize(self.current_file) if os.path.exists(self.current_file) else 0
    
    def stop_recording(self, audio_file_path=None, on_merge_complete=None):
        self.is_writing = False
        if self.writer:
            self.writer.release()
            self.writer = None
        
        duration = time.time() - self.start_time if self.start_time else 0
        
        result = {
            "file": self.current_file,
            "frames": self.frame_count,
            "duration": duration,
            "file_size": self.file_size
        }
        
        if audio_file_path and os.path.exists(audio_file_path):
            merge_thread = threading.Thread(
                target=self._merge_audio_async,
                args=(audio_file_path, on_merge_complete),
                daemon=True
            )
            merge_thread.start()
        
        return result
    
    def _merge_audio_async(self, audio_file_path, on_merge_complete=None):
        try:
            self._merge_audio(audio_file_path)
            if on_merge_complete:
                on_merge_complete(self.current_file)
        except Exception as e:
            logger.error(f"Async merge error: {e}")
            if on_merge_complete:
                on_merge_complete(None)
    
    def _merge_audio(self, audio_file_path):
        try:
            logger.info(f"Merging audio from: {audio_file_path}")
            logger.info(f"Video file: {self.current_file}")
            
            try:
                from moviepy import VideoFileClip, AudioFileClip
                logger.info("Imported from moviepy (v2.x)")
            except ImportError as e:
                logger.info(f"Import from moviepy failed: {e}")
                try:
                    from moviepy.editor import VideoFileClip, AudioFileClip
                    logger.info("Imported from moviepy.editor (v1.x)")
                except ImportError as e2:
                    logger.error(f"Import from moviepy.editor failed: {e2}")
                    raise
            
            temp_file = self.current_file.replace(f".{self.format}", "_temp.mp4")
            
            video_clip = VideoFileClip(self.current_file)
            audio_clip = AudioFileClip(audio_file_path)
            
            logger.info(f"Video duration: {video_clip.duration}s, Audio duration: {audio_clip.duration}s")
            
            final_clip = video_clip.with_audio(audio_clip)
            final_clip.write_videofile(
                temp_file,
                codec="libx264",
                audio_codec="aac",
                fps=self.fps,
                logger=None
            )
            
            video_clip.close()
            audio_clip.close()
            final_clip.close()
            
            if os.path.exists(temp_file):
                logger.info("Merge successful, replacing original file")
                if os.path.exists(self.current_file):
                    os.remove(self.current_file)
                os.rename(temp_file, self.current_file)
                self.file_size = os.path.getsize(self.current_file)
                
                if os.path.exists(audio_file_path):
                    os.remove(audio_file_path)
                    logger.info(f"Cleaned up audio file: {audio_file_path}")
            else:
                logger.error("Merge failed: temp file not created")
        except ImportError:
            logger.info("moviepy not installed. Video saved without audio.")
        except Exception as e:
            import traceback
            logger.error(f"Failed to merge audio: {e}")
            traceback.print_exc()
    
    def get_file_size(self):
        if self.current_file and os.path.exists(self.current_file):
            return os.path.getsize(self.current_file)
        return 0
    
    def get_output_dir(self):
        return self.output_dir
