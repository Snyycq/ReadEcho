"""
ReadEcho Pro 录音管理模块
处理录音相关的功能：录音保存、音频文件处理
"""

import time
import numpy as np
import sounddevice as sd
from scipy.io.wavfile import write
from PyQt6.QtCore import QThread, pyqtSignal

from config import SAMPLE_RATE, TEMP_AUDIO_FILE, RECORDING_DURATION


class RecordingFinishThread(QThread):
    """处理录音完成的后台线程，避免阻塞UI"""

    recording_ready = pyqtSignal(str)  # 发出音频文件路径

    def __init__(self, recording_data, fs, file_path):
        """
        初始化录音完成线程

        Args:
            recording_data: 录音数据（numpy数组）
            fs: 采样率
            file_path: 保存音频文件的路径
        """
        super().__init__()
        self.recording_data = recording_data
        self.fs = fs
        self.file_path = file_path

    def run(self):
        """在后台线程中保存录音文件"""
        try:
            # 立即停止录音，不要等待
            sd.stop()

            # 小延迟，确保数据被完全读取
            time.sleep(0.1)

            # 直接保存，不裁剪
            write(self.file_path, self.fs, self.recording_data)
            self.recording_ready.emit(self.file_path)
        except Exception as e:
            err_msg = f"Error: {str(e)}"
            self.recording_ready.emit(err_msg)


class RecordingService:
    """录音服务管理器，提供录音相关功能"""

    def __init__(self):
        self.fs = SAMPLE_RATE
        self.is_recording = False
        self.recording_data = None
        self.recording_thread = None

    def start_recording(self):
        """开始录音"""
        self.is_recording = True
        # 预分配录音缓冲区
        self.recording_data = sd.rec(
            int(RECORDING_DURATION * self.fs), samplerate=self.fs, channels=1, dtype=np.float32
        )
        return True

    def stop_recording(self):
        """停止录音并返回录音完成线程"""
        self.is_recording = False
        # 创建后台线程处理录音保存
        self.recording_thread = RecordingFinishThread(self.recording_data, self.fs, TEMP_AUDIO_FILE)
        return self.recording_thread

    def get_recording_status(self):
        """获取录音状态"""
        return self.is_recording

    def cleanup(self):
        """清理录音资源"""
        if self.is_recording:
            sd.stop()
            self.is_recording = False
        self.recording_data = None
