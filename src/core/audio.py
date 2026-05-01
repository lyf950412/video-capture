import numpy as np
import threading
import time
import wave
import os
import sounddevice as sd


class AudioCapture:
    def __init__(self, sample_rate=44100, channels=2, chunk_size=1024, mic_volume=80, sys_volume=100):
        self.sample_rate = sample_rate
        self.channels = channels
        self.chunk_size = chunk_size
        self.mic_volume = mic_volume / 100.0
        self.sys_volume = sys_volume / 100.0
        self.running = False
        self.audio_thread = None
        self.audio_callback = None
        self.mic_enabled = True
        self.sys_audio_enabled = True
        
        self.audio_frames = []
        self.audio_file_path = None
        self.stream = None
    
    def set_audio_callback(self, callback):
        self.audio_callback = callback
    
    def get_available_devices(self):
        devices = []
        for device in sd.query_devices():
            if device['max_input_channels'] > 0:
                devices.append({
                    'index': device['index'],
                    'name': device['name'],
                    'channels': device['max_input_channels']
                })
        return devices
    
    def _select_best_device(self):
        devices = sd.query_devices()
        
        print("Available input devices:")
        for i, device in enumerate(devices):
            if device['max_input_channels'] > 0:
                print(f"  [{i}] {device['name']}")
        
        priority_keywords = [
            'loopback',
            '立体声混音', 'stereo mix',
            'wasapi',
            '扬声器', 'speaker',
            '线路输入', 'line in',
            '麦克风', 'microphone', 'mic'
        ]
        
        best_device = None
        best_score = -1
        
        for i, device in enumerate(devices):
            if device['max_input_channels'] == 0:
                continue
            
            name = device['name'].lower()
            score = 0
            
            for idx, keyword in enumerate(priority_keywords):
                if keyword in name:
                    score = len(priority_keywords) - idx
                    break
            
            if score > best_score:
                best_score = score
                best_device = i
        
        if best_device is not None:
            selected = devices[best_device]
            print(f"Auto-selected device: [{best_device}] {selected['name']}")
            return best_device
        else:
            print("Using default input device")
            return None
    
    def start(self, audio_file_path=None):
        self.running = True
        self.audio_frames = []
        self.audio_file_path = audio_file_path
        self.audio_thread = threading.Thread(target=self._audio_loop, daemon=True)
        self.audio_thread.start()
    
    def stop(self):
        self.running = False
        if self.stream:
            self.stream.stop()
            self.stream.close()
            self.stream = None
        if self.audio_thread:
            self.audio_thread.join(timeout=2.0)
        
        if self.audio_frames and self.audio_file_path:
            self._save_audio_file()
    
    def _save_audio_file(self):
        try:
            with wave.open(self.audio_file_path, 'wb') as wf:
                wf.setnchannels(self.channels)
                wf.setsampwidth(2)
                wf.setframerate(self.sample_rate)
                wf.writeframes(b''.join(self.audio_frames))
            print(f"Audio saved to: {self.audio_file_path}")
        except Exception as e:
            print(f"Failed to save audio file: {e}")
    
    def _audio_loop(self):
        try:
            device_id = self._select_best_device()
            
            print(f"Starting audio capture: device={device_id}, sample_rate={self.sample_rate}, channels={self.channels}")
            
            def callback(indata, frames, time_info, status):
                if status:
                    print(f"Audio status: {status}")
                
                if self.running and indata is not None:
                    audio_data = (indata * 32767).astype(np.int16)
                    
                    if audio_data.ndim == 2 and audio_data.shape[1] > 1:
                        audio_data = audio_data.mean(axis=1).astype(np.int16)
                    
                    audio_bytes = audio_data.tobytes()
                    self.audio_frames.append(audio_bytes)
                    
                    if self.audio_callback:
                        if self.sys_audio_enabled and not self.mic_enabled:
                            audio_data = (audio_data * self.sys_volume).astype(np.int16)
                        elif self.mic_enabled and not self.sys_audio_enabled:
                            audio_data = (audio_data * self.mic_volume).astype(np.int16)
                        else:
                            volume = max(self.mic_volume, self.sys_volume)
                            audio_data = (audio_data * volume).astype(np.int16)
                        self.audio_callback(audio_data.tobytes())
            
            with sd.InputStream(
                device=device_id,
                channels=self.channels,
                samplerate=self.sample_rate,
                dtype='float32',
                callback=callback,
                blocksize=self.chunk_size
            ):
                print("Audio stream started")
                while self.running:
                    time.sleep(0.1)
            
        except Exception as e:
            print(f"Audio capture error: {e}")
            import traceback
            traceback.print_exc()
    
    def set_mic_volume(self, volume):
        self.mic_volume = volume / 100.0
    
    def set_sys_volume(self, volume):
        self.sys_volume = volume / 100.0
    
    def cleanup(self):
        if self.stream:
            self.stream.close()
