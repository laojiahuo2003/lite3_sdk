"""摄像头视频流客户端"""
import os
import threading
import time
from typing import Optional, Callable, Tuple
import cv2
import numpy as np


class CameraClient:
    """Lite3机器人摄像头客户端"""

    def __init__(self, host: str = "192.168.2.1", port: int = 8554, stream_name: str = "test"):
        """
        初始化摄像头客户端

        Args:
            host: 运动主机IP地址
            port: RTSP端口
            stream_name: 视频流名称
        """
        self.rtsp_url = f"rtsp://{host}:{port}/{stream_name}"
        self.cap: Optional[cv2.VideoCapture] = None
        self.receive_thread: Optional[threading.Thread] = None
        self.is_receiving = False
        self.frame_callback: Optional[Callable[[np.ndarray], None]] = None
        self._latest_frame: Optional[np.ndarray] = None
        self._frame_lock = threading.Lock()

        # 强制使用 TCP 传输 RTSP 流（比 UDP 更可靠，尤其是 WSL2/跨网段场景）
        os.environ.setdefault("OPENCV_FFMPEG_CAPTURE_OPTIONS", "rtsp_transport;tcp")

    def connect(self, timeout: float = 10.0) -> bool:
        """
        连接摄像头视频流

        Args:
            timeout: 连接超时时间（秒），默认 10s

        Returns:
            是否连接成功
        """
        try:
            self.cap = cv2.VideoCapture(self.rtsp_url, cv2.CAP_FFMPEG)

            # 设置超时（OpenCV >= 4.7 支持，旧版本静默忽略）
            try:
                self.cap.set(cv2.CAP_PROP_OPEN_TIMEOUT_MS, int(timeout * 1000))
                self.cap.set(cv2.CAP_PROP_READ_TIMEOUT_MS, int(timeout * 1000))
            except Exception:
                pass

            if not self.cap.isOpened():
                print(f"无法连接摄像头: {self.rtsp_url}")
                print("可能的原因：")
                print("  1. 机器狗未开机或摄像头未启动")
                print("  2. WSL2 网络不通 — 尝试在 Windows 端用 VLC 测试 rtsp://192.168.2.1:8554/test")
                print("  3. 防火墙阻止了 8554 端口")
                return False

            # 设置缓冲区大小（减少延迟）
            self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

            # 实际读取一帧来验证连接（RTSP 流 isOpened() 可能欺骗性地返回 True）
            start_time = time.time()
            ret, frame = self.cap.read()
            if not ret:
                elapsed = time.time() - start_time
                print(f"无法从摄像头读取视频帧 (等待了 {elapsed:.1f}s): {self.rtsp_url}")
                print("RTSP 连接已建立但无法获取视频数据，通常是因为：")
                print("  1. UDP RTP 包被防火墙/NAT 丢弃 — 已自动使用 TCP 传输")
                print("  2. 如果仍然失败，请在 Windows 宿主端用 VLC 测试是否能拉流")
                self.cap.release()
                self.cap = None
                return False

            self._latest_frame = frame
            print(f"摄像头连接成功: {self.rtsp_url} (分辨率: {frame.shape[1]}x{frame.shape[0]})")
            return True
        except Exception as e:
            print(f"连接摄像头失败: {e}")
            return False

    def disconnect(self):
        """断开摄像头连接"""
        self.stop_receiving()
        if self.cap:
            self.cap.release()
            self.cap = None

    def read_frame(self) -> Optional[np.ndarray]:
        """
        读取一帧图像（阻塞）

        Returns:
            图像帧，失败返回None
        """
        if not self.cap or not self.cap.isOpened():
            return None

        ret, frame = self.cap.read()
        return frame if ret else None

    def get_latest_frame(self) -> Optional[np.ndarray]:
        """
        获取最新的一帧图像（非阻塞）

        Returns:
            图像帧，失败返回None
        """
        with self._frame_lock:
            return self._latest_frame.copy() if self._latest_frame is not None else None

    def set_frame_callback(self, callback: Optional[Callable[[np.ndarray], None]]):
        """
        设置帧回调函数

        Args:
            callback: 回调函数，签名为 callback(frame: np.ndarray)
        """
        self.frame_callback = callback

    def start_receiving(self):
        """开始接收视频流（异步）"""
        if self.is_receiving:
            return

        if not self.cap or not self.cap.isOpened():
            print("摄像头未连接")
            return

        self.is_receiving = True
        self.receive_thread = threading.Thread(target=self._receive_loop, daemon=True)
        self.receive_thread.start()

    def stop_receiving(self):
        """停止接收视频流"""
        self.is_receiving = False
        if self.receive_thread:
            self.receive_thread.join(timeout=2.0)
            self.receive_thread = None

    def _receive_loop(self):
        """接收视频流循环"""
        while self.is_receiving and self.cap and self.cap.isOpened():
            ret, frame = self.cap.read()
            if ret:
                with self._frame_lock:
                    self._latest_frame = frame

                if self.frame_callback:
                    try:
                        self.frame_callback(frame)
                    except Exception as e:
                        print(f"帧回调函数执行失败: {e}")
            else:
                # 连接断开，尝试重连
                print("视频流断开，尝试重连...")
                time.sleep(1.0)
                self.cap.release()
                self.cap = cv2.VideoCapture(self.rtsp_url, cv2.CAP_FFMPEG)
                self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                if not self.cap.isOpened():
                    print("重连失败")
                    self.is_receiving = False
                    break

    def get_frame_info(self) -> Optional[Tuple[int, int, float]]:
        """
        获取视频帧信息

        Returns:
            (宽度, 高度, 帧率) 或 None
        """
        if not self.cap or not self.cap.isOpened():
            return None

        width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = self.cap.get(cv2.CAP_PROP_FPS)
        return (width, height, fps)

    def __enter__(self):
        """上下文管理器入口"""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.disconnect()