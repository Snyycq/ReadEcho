"""
ReadEcho Pro 录音管理模块
处理录音相关的功能：录音保存、音频文件处理
"""

import time
import numpy as np
import sounddevice as sd
from scipy.io.wavfile import write
from PyQt6.QtCore import QThread, pyqtSignal

from config import SAMPLE_RATE, TEMP_AUDIO_FILE, LOGGER


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
            LOGGER.debug(f"[DEBUG-录音] 开始保存录音文件: {self.file_path}")
            LOGGER.debug(f"[DEBUG-录音] 录音数据类型: {type(self.recording_data)}")

            # 立即停止录音，不要等待
            sd.stop()
            LOGGER.debug("[DEBUG-录音] 音频流已停止")

            # 小延迟，确保数据被完全读取
            time.sleep(0.1)

            # 检查录音数据
            if self.recording_data is None:
                LOGGER.error("[DEBUG-录音] 录音数据为 None")
                self.recording_ready.emit("Error: 录音数据为空")
                return

            if len(self.recording_data) == 0:
                LOGGER.error("[DEBUG-录音] 录音数据长度为 0")
                self.recording_ready.emit("Error: 录音数据为空")
                return

            LOGGER.debug(f"[DEBUG-录音] 录音数据长度: {len(self.recording_data)}")

            # 保存录音文件
            write(self.file_path, self.fs, self.recording_data)
            LOGGER.debug(f"[DEBUG-录音] 录音文件保存成功: {self.file_path}")
            self.recording_ready.emit(self.file_path)
        except Exception as e:
            LOGGER.error(f"[DEBUG-录音] 保存录音失败: {e}", exc_info=True)
            err_msg = f"Error: {str(e)}"
            self.recording_ready.emit(err_msg)


class RecordingService:
    """录音服务管理器，提供录音相关功能"""

    def __init__(self):
        self.fs = SAMPLE_RATE
        self.is_recording = False
        self.recording_data = None
        self.recording_thread = None
        self.recording_frames = []
        self.audio_stream = None

    def start_recording(self):
        """开始录音（非阻塞）"""
        try:
            LOGGER.debug("[DEBUG-录音服务] 开始录音...")
            self.is_recording = True
            # 使用 callback 方式录音，避免阻塞 UI
            self.recording_frames = []

            def audio_callback(indata, frames, time_info, status):
                if self.is_recording:
                    self.recording_frames.append(indata.copy())

            self.audio_stream = sd.InputStream(
                samplerate=self.fs, channels=1, dtype=np.float32, callback=audio_callback
            )
            self.audio_stream.start()
            LOGGER.debug("[DEBUG-录音服务] 音频流启动成功")
            return True
        except Exception as e:
            LOGGER.error(f"[DEBUG-录音服务] 启动录音失败: {e}", exc_info=True)
            self.is_recording = False
            return False

    def stop_recording(self):
        """停止录音并返回录音完成线程"""
        LOGGER.debug("[DEBUG-录音服务] 停止录音...")
        self.is_recording = False

        # 停止音频流
        if hasattr(self, "audio_stream") and self.audio_stream:
            self.audio_stream.stop()
            self.audio_stream.close()
            self.audio_stream = None
            LOGGER.debug("[DEBUG-录音服务] 音频流已关闭")

        # 合并录音帧
        if self.recording_frames:
            self.recording_data = np.concatenate(self.recording_frames, axis=0)
            frames_count = len(self.recording_frames)
            data_len = len(self.recording_data)
            LOGGER.debug(f"[DEBUG-录音服务] 合并录音帧: {frames_count} 帧, 数据长度: {data_len}")
        else:
            self.recording_data = np.array([], dtype=np.float32)
            LOGGER.warning("[DEBUG-录音服务] 没有录音帧")

        # 创建后台线程处理录音保存
        self.recording_thread = RecordingFinishThread(self.recording_data, self.fs, TEMP_AUDIO_FILE)
        LOGGER.debug(f"[DEBUG-录音服务] 创建录音保存线程: {self.recording_thread}")
        return self.recording_thread

    def get_recording_status(self):
        """获取录音状态"""
        return self.is_recording

    def cleanup(self):
        """清理录音资源"""
        if self.is_recording:
            self.is_recording = False
        if hasattr(self, "audio_stream") and self.audio_stream:
            try:
                self.audio_stream.stop()
                self.audio_stream.close()
            except Exception:
                pass
            self.audio_stream = None
        self.recording_data = None
        self.recording_frames = []
