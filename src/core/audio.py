import numpy as np
import threading
import time
import wave
import os
import logging
from collections import deque
import sounddevice as sd

logger = logging.getLogger(__name__)


class AudioCapture:
    """双流音频采集器：同时录制系统声音（loopback）+ 麦克风，并实时混音"""

    def __init__(self, sample_rate=44100, channels=2, chunk_size=1024,
                 mic_volume=80, sys_volume=100):
        self.sample_rate = sample_rate
        self.channels = channels
        self.chunk_size = chunk_size
        self.mic_volume = mic_volume / 100.0
        self.sys_volume = sys_volume / 100.0
        self.running = False
        self.audio_callback = None
        self.mic_enabled = True
        self.sys_audio_enabled = True

        # 混音后的音频帧
        self.audio_frames = []
        self.audio_file_path = None

        # 两路独立的帧缓冲（用于混音线程取数据）
        self._sys_deque = deque()
        self._mic_deque = deque()
        self._mix_lock = threading.Lock()
        self._mix_signal = threading.Condition(threading.Lock())

        # 两个独立的流和线程
        self._sys_stream = None
        self._mic_stream = None
        self._sys_thread = None
        self._mic_thread = None
        self._mixer_thread = None

        # 设备 ID（启动时探测）
        self._sys_device_id = None
        self._mic_device_id = None

    def set_audio_callback(self, callback):
        self.audio_callback = callback

    def get_available_devices(self):
        """获取所有可用输入设备"""
        devices = []
        for device in sd.query_devices():
            if device['max_input_channels'] > 0:
                devices.append({
                    'index': device['index'],
                    'name': device['name'],
                    'channels': device['max_input_channels'],
                    'hostapi': device.get('hostapi', -1),
                })
        return devices

    def _detect_devices(self):
        """自动探测系统音频设备（loopback）和麦克风设备"""
        devices = sd.query_devices()
        hostapis = sd.query_hostapis()

        logger.info("可用输入设备:")
        for i, device in enumerate(devices):
            if device['max_input_channels'] > 0:
                api_name = hostapis[device['hostapi']]['name'] if device['hostapi'] >= 0 else '?'
                logger.info(f"  [{i}] {device['name']} "
                            f"(in={device['max_input_channels']}, api={api_name})")

        sys_device = None
        mic_device = None

        # ---- 第一轮：找 loopback 系统声音设备 ----
        for i, device in enumerate(devices):
            if device['max_input_channels'] == 0:
                continue
            name = device['name'].lower()
            sys_keywords = ['loopback', '立体声混音', 'stereo mix',
                            'what u hear', 'wave out', 'wasapi loopback']
            for kw in sys_keywords:
                if kw in name:
                    sys_device = i
                    logger.info(f"系统声音设备: [{i}] {device['name']}")
                    break
            if sys_device is not None:
                break

        # ---- 第二轮：找麦克风设备（与 sys_device 不能重复）----
        for i, device in enumerate(devices):
            if device['max_input_channels'] == 0:
                continue
            if i == sys_device:
                continue
            name = device['name'].lower()
            mic_keywords = ['麦克风', 'microphone', 'mic', 'headset',
                            'headphone', '外部', 'internal mic']
            for kw in mic_keywords:
                if kw in name:
                    mic_device = i
                    logger.info(f"麦克风设备: [{i}] {device['name']}")
                    break
            if mic_device is not None:
                break

        # 若还没找到麦克风，回退到默认输入设备
        if mic_device is None:
            try:
                default_input = sd.default.device[0]
                if (default_input is not None
                        and default_input != sys_device
                        and devices[default_input]['max_input_channels'] > 0):
                    mic_device = default_input
                    logger.info(f"麦克风设备(默认): [{mic_device}] {devices[mic_device]['name']}")
            except Exception:
                pass

        self._sys_device_id = sys_device
        self._mic_device_id = mic_device

        logger.info(f"最终设备: sys={sys_device}, mic={mic_device}")

    def start(self, audio_file_path=None):
        self.running = True
        if audio_file_path is not None:
            self.audio_frames = []
            self.audio_file_path = audio_file_path

        # 清空缓冲
        self._sys_deque.clear()
        self._mic_deque.clear()

        # 探测设备
        self._detect_devices()

        # 启动混音线程（始终启动，处理可用的流）
        self._mixer_thread = threading.Thread(
            target=self._mixer_loop, daemon=True
        )
        self._mixer_thread.start()

        # 启动系统音频流
        if self.sys_audio_enabled and self._sys_device_id is not None:
            self._sys_thread = threading.Thread(
                target=self._stream_loop,
                args=('sys', self._sys_device_id, self.sys_volume, self._sys_deque),
                daemon=True
            )
            self._sys_thread.start()
        elif self.sys_audio_enabled:
            logger.warning("未找到系统声音(Loopback)设备，系统声音不会被录制。"
                           "请确认在 Windows 声音设置中已启用立体声混音。")

        # 启动麦克风流
        if self.mic_enabled and self._mic_device_id is not None:
            self._mic_thread = threading.Thread(
                target=self._stream_loop,
                args=('mic', self._mic_device_id, self.mic_volume, self._mic_deque),
                daemon=True
            )
            self._mic_thread.start()
        elif self.mic_enabled:
            logger.warning("未找到麦克风设备，麦克风不会被录制。")

    def _stream_loop(self, tag, device_id, volume, output_deque):
        """单个音频流的采集循环，将 int16 bytes 放入队列"""
        try:
            logger.info(f"[{tag}] 启动音频流: device={device_id}, volume={volume:.2f}")

            def callback(indata, frames, time_info, status):
                if status:
                    logger.warning(f"[{tag}] Audio status: {status}")
                if not self.running or indata is None:
                    return

                # float32 → int16
                audio_data = (indata * 32767).astype(np.int16)

                # 多声道 → 单声道
                if audio_data.ndim == 2 and audio_data.shape[1] > 1:
                    audio_data = audio_data.mean(axis=1).astype(np.int16)

                # 应用音量
                if volume != 1.0:
                    audio_data = (audio_data * volume).astype(np.int16)

                # 放入队列，通知混音线程
                with self._mix_signal:
                    output_deque.append(audio_data.tobytes())
                    self._mix_signal.notify()

            stream = sd.InputStream(
                device=device_id,
                channels=self.channels,
                samplerate=self.sample_rate,
                dtype='float32',
                callback=callback,
                blocksize=self.chunk_size,
            )

            if tag == 'sys':
                self._sys_stream = stream
            else:
                self._mic_stream = stream

            with stream:
                logger.info(f"[{tag}] 音频流已启动")
                while self.running:
                    time.sleep(0.1)

        except Exception as e:
            logger.error(f"[{tag}] 音频流错误: {e}")
            import traceback
            traceback.print_exc()

    def _mixer_loop(self):
        """混音线程：从两路队列取数据，逐采样点相加后写入 audio_frames"""
        logger.info("混音线程已启动")

        while self.running:
            with self._mix_signal:
                # 等待任意一路有新数据
                if not self._sys_deque and not self._mic_deque:
                    self._mix_signal.wait(timeout=0.5)
                    continue

                # 尽量取出对齐的数据量
                mixed = self._mix_buffers()

            if mixed is not None:
                self.audio_frames.append(mixed)

                # 通知外部回调（混音后的数据）
                if self.audio_callback:
                    self.audio_callback(mixed)

        logger.info("混音线程已停止")

    def _mix_buffers(self):
        """从两路 deque 中各取一个 block，逐采样相加"""
        sys_bytes = self._sys_deque.popleft() if self._sys_deque else None
        mic_bytes = self._mic_deque.popleft() if self._mic_deque else None

        if sys_bytes is None and mic_bytes is None:
            return None

        # 只有一路有数据，直接返回
        if sys_bytes is None:
            return mic_bytes
        if mic_bytes is None:
            return sys_bytes

        # 两路都有数据，转换为 numpy 数组进行逐采样点相加
        sys_arr = np.frombuffer(sys_bytes, dtype=np.int16).astype(np.float32)
        mic_arr = np.frombuffer(mic_bytes, dtype=np.int16).astype(np.float32)

        # 取较短数组的长度对齐
        min_len = min(len(sys_arr), len(mic_arr))
        sys_arr = sys_arr[:min_len]
        mic_arr = mic_arr[:min_len]

        # 混音：相加并裁剪到 int16 范围，防止溢出
        mixed = sys_arr + mic_arr
        mixed = np.clip(mixed, -32768, 32767).astype(np.int16)

        return mixed.tobytes()

    def stop(self):
        self.running = False

        # 唤醒混音线程使其退出
        with self._mix_signal:
            self._mix_signal.notify()

        # 关闭系统音频流
        if self._sys_stream:
            try:
                self._sys_stream.stop()
                self._sys_stream.close()
            except Exception:
                pass
            self._sys_stream = None

        # 关闭麦克风流
        if self._mic_stream:
            try:
                self._mic_stream.stop()
                self._mic_stream.close()
            except Exception:
                pass
            self._mic_stream = None

        # 等待线程结束
        for t in (self._sys_thread, self._mic_thread, self._mixer_thread):
            if t and t.is_alive():
                t.join(timeout=2.0)

    def save(self):
        """保存累积的音频帧到 WAV 文件"""
        if self.audio_frames and self.audio_file_path:
            self._save_audio_file()

    def _save_audio_file(self):
        try:
            os.makedirs(os.path.dirname(self.audio_file_path), exist_ok=True)
            with wave.open(self.audio_file_path, 'wb') as wf:
                wf.setnchannels(self.channels)
                wf.setsampwidth(2)
                wf.setframerate(self.sample_rate)
                wf.writeframes(b''.join(self.audio_frames))
            logger.info(f"音频文件已保存: {self.audio_file_path} "
                        f"({len(self.audio_frames)} 帧)")
        except Exception as e:
            logger.error(f"保存音频文件失败: {e}")

    def set_mic_volume(self, volume):
        self.mic_volume = volume / 100.0

    def set_sys_volume(self, volume):
        self.sys_volume = volume / 100.0

    def cleanup(self):
        if self._sys_stream:
            try:
                self._sys_stream.close()
            except Exception:
                pass
        if self._mic_stream:
            try:
                self._mic_stream.close()
            except Exception:
                pass
