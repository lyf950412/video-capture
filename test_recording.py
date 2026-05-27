import sys
import os
import time
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.core.capture import ScreenCapture
from src.core.encoder import VideoEncoder


def test_recording():
    print("=" * 50)
    print("CapSure - 录制功能测试")
    print("=" * 50)
    
    output_dir = os.path.join(os.path.expanduser("~"), "Videos", "CapSure")
    os.makedirs(output_dir, exist_ok=True)
    
    test_file = os.path.join(output_dir, "test_recording.mp4")
    
    if os.path.exists(test_file):
        os.remove(test_file)
    
    fps = 30
    duration = 5
    frames_captured = [0]
    frames_encoded = [0]
    
    encoder = VideoEncoder(output_dir=output_dir, fps=fps, format="mp4")
    
    def on_frame(frame):
        frames_captured[0] += 1
        encoder.write_frame(frame)
        frames_encoded[0] += 1
    
    capture = ScreenCapture(fps=fps)
    capture.set_frame_callback(on_frame)
    
    monitor_info = capture.get_monitor_info()
    print(f"\n屏幕分辨率: {monitor_info['width']}x{monitor_info['height']}")
    print(f"帧率: {fps} FPS")
    print(f"测试时长: {duration} 秒")
    print(f"\n开始录制...")
    
    encoder.start_recording(monitor_info["width"], monitor_info["height"])
    capture.start()
    
    start_time = time.time()
    while time.time() - start_time < duration:
        time.sleep(0.1)
        elapsed = time.time() - start_time
        print(f"\r已录制: {elapsed:.1f}/{duration}秒, 帧数: {frames_captured[0]}", end="", flush=True)
    
    print("\n\n停止录制...")
    capture.stop()
    result = encoder.stop_recording()
    
    print(f"\n录制结果:")
    print(f"  - 文件: {result['file']}")
    print(f"  - 帧数: {result['frames']}")
    print(f"  - 时长: {result['duration']:.2f}秒")
    print(f"  - 文件大小: {result['file_size'] / (1024*1024):.2f} MB")
    
    if os.path.exists(result['file']):
        print(f"\n✓ 录制成功! 视频文件已保存")
        print(f"  路径: {result['file']}")
    else:
        print(f"\n✗ 录制失败! 文件未生成")
    
    print("=" * 50)
    
    return os.path.exists(result['file'])


if __name__ == "__main__":
    success = test_recording()
    sys.exit(0 if success else 1)
