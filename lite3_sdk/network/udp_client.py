"""UDP通信客户端"""
import socket
import struct
import threading
from typing import Optional, Tuple, Callable
from dataclasses import dataclass


@dataclass
class CommandHead:
    """指令头部结构"""
    code: int  # 指令码
    parameters_size: int  # 参数大小
    type: int  # 指令类型 (0: 简单指令, 1: 复杂指令)

    def pack(self) -> bytes:
        """打包为字节序列（parameters_size 用有符号格式以支持负轴值）"""
        return struct.pack('<IiI', self.code, self.parameters_size, self.type)


@dataclass
class Command:
    """复杂指令结构"""
    head: CommandHead
    data: bytes

    def pack(self) -> bytes:
        """打包为字节序列"""
        return self.head.pack() + self.data


class UDPClient:
    """UDP客户端"""

    def __init__(self, host: str, port: int, timeout: float = 1.0):
        """
        初始化UDP客户端

        Args:
            host: 目标主机IP
            port: 目标端口
            timeout: 超时时间(秒)
        """
        self.host = host
        self.port = port
        self.timeout = timeout
        self.socket: Optional[socket.socket] = None
        self.receive_thread: Optional[threading.Thread] = None
        self.is_receiving = False
        self.message_handlers: dict = {}  # 指令码 -> 处理函数

    def connect(self, verify: bool = True) -> bool:
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.socket.bind(('0.0.0.0', 0))

            if not verify:
                self.socket.settimeout(0.02)  # 接收循环用短超时
                return True

            # 发送心跳包验证连接
            self.socket.settimeout(self.timeout)
            heartbeat = CommandHead(code=0x21040001, parameters_size=0, type=0)
            self.socket.sendto(heartbeat.pack(), (self.host, self.port))

            try:
                self.socket.recvfrom(4096)
                print(f"✅ 收到响应，目标主机可达")
            except socket.timeout:
                print(f"⚠️  未收到响应（超时{self.timeout}秒）")
                print(f"   可能原因：")
                print(f"   1. 机器狗未开机或网络不通")
                print(f"   2. 机器狗开机但未配置数据上报")
                return False
            except OSError as e:
                print(f"❌ 连接验证失败: {e}")
                return False

            # 验证完成，切换到短超时以适应高频数据接收
            self.socket.settimeout(0.02)
            return True

        except OSError as e:
            print(f"连接失败: {e}")
            return False

    def disconnect(self):
        """断开连接"""
        self.stop_receiving()
        if self.socket:
            try:
                self.socket.close()
            except OSError:
                pass
            self.socket = None

    def send_simple_command(self, code: int, parameters_size: int = 0) -> bool:
        """
        发送简单指令

        Args:
            code: 指令码
            parameters_size: 参数大小

        Returns:
            是否发送成功
        """
        if not self.socket:
            print("未连接")
            return False

        try:
            command = CommandHead(code=code, parameters_size=parameters_size, type=0)
            data = command.pack()
            self.socket.sendto(data, (self.host, self.port))
            return True
        except Exception as e:
            print(f"发送简单指令失败: {e}")
            return False

    def send_complex_command(self, code: int, data: bytes) -> bool:
        """
        发送复杂指令

        Args:
            code: 指令码
            data: 数据内容

        Returns:
            是否发送成功
        """
        if not self.socket:
            print("未连接")
            return False

        try:
            head = CommandHead(code=code, parameters_size=len(data), type=1)
            command = Command(head=head, data=data)
            packed_data = command.pack()
            self.socket.sendto(packed_data, (self.host, self.port))
            return True
        except Exception as e:
            print(f"发送复杂指令失败: {e}")
            return False

    def register_handler(self, code: int, handler: Callable):
        """
        注册消息处理函数

        Args:
            code: 指令码
            handler: 处理函数，签名为 handler(code: int, data: bytes)
        """
        self.message_handlers[code] = handler

    def unregister_handler(self, code: int):
        """注销消息处理函数"""
        if code in self.message_handlers:
            del self.message_handlers[code]

    def _receive_loop(self):
        """接收消息循环"""
        while self.is_receiving and self.socket:
            try:
                data, addr = self.socket.recvfrom(4096)
                if len(data) < 12:  # 至少需要12字节的头部
                    continue

                # 解析头部
                code, parameters_size, msg_type = struct.unpack('<III', data[:12])

                # 如果是复杂指令且有数据
                if msg_type == 1 and len(data) >= 12 + parameters_size:
                    message_data = data[12:12 + parameters_size]
                else:
                    message_data = b''

                # 调用对应的处理函数
                if code in self.message_handlers:
                    try:
                        self.message_handlers[code](code, message_data)
                    except Exception as e:
                        print(f"处理消息失败: code=0x{code:08X}, error={e}")

            except socket.timeout:
                continue
            except Exception as e:
                if self.is_receiving:  # 只有在正在接收时才打印错误
                    print(f"接收消息失败: {e}")

    def start_receiving(self):
        """开始接收消息"""
        if self.is_receiving:
            return

        self.is_receiving = True
        self.receive_thread = threading.Thread(target=self._receive_loop, daemon=True)
        self.receive_thread.start()

    def stop_receiving(self):
        """停止接收消息"""
        self.is_receiving = False
        if self.receive_thread:
            self.receive_thread.join(timeout=2.0)
            self.receive_thread = None

    def receive_once(self, timeout: Optional[float] = None) -> Optional[Tuple[int, bytes]]:
        """
        接收一次消息（阻塞）

        Args:
            timeout: 超时时间，None表示使用默认超时

        Returns:
            (指令码, 数据) 或 None
        """
        if not self.socket:
            return None

        old_timeout = self.socket.gettimeout()
        if timeout is not None:
            self.socket.settimeout(timeout)

        try:
            data, addr = self.socket.recvfrom(4096)
            if len(data) < 12:
                return None

            code, parameters_size, msg_type = struct.unpack('<III', data[:12])

            if msg_type == 1 and len(data) >= 12 + parameters_size:
                message_data = data[12:12 + parameters_size]
            else:
                message_data = b''

            return (code, message_data)
        except socket.timeout:
            return None
        except Exception as e:
            print(f"接收消息失败: {e}")
            return None
        finally:
            self.socket.settimeout(old_timeout)

    def __enter__(self):
        """上下文管理器入口"""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.disconnect()