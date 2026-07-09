"""UDP通信客户端"""
import socket
import struct
import threading
import time as _time
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

    def __init__(self, host: str, port: int, timeout: float = 1.0,
                 packet_log_path: Optional[str] = None,
                 local_port: int = 0):
        """
        初始化UDP客户端

        Args:
            host: 目标主机IP
            port: 目标端口
            timeout: 超时时间(秒)
            packet_log_path: 收包日志文件路径（None 则不记录）
            local_port: 本机绑定端口（0=随机端口）
        """
        self.host = host
        self.port = port
        self.timeout = timeout
        self.local_port = local_port
        self.socket: Optional[socket.socket] = None
        self.receive_thread: Optional[threading.Thread] = None
        self.is_receiving = False
        self.message_handlers: dict = {}  # 指令码 -> 处理函数
        self._packet_log_path = packet_log_path
        self._packet_log_file = None
        self._packet_count = 0
        self._last_log_flush = 0.0

    # =========================================================================
    # 收包日志（调试用）
    # =========================================================================

    def _open_packet_log(self):
        """打开收包日志文件"""
        if self._packet_log_path:
            import os
            log_dir = os.path.dirname(self._packet_log_path)
            if log_dir:
                os.makedirs(log_dir, exist_ok=True)
            self._packet_log_file = open(self._packet_log_path, 'a', encoding='utf-8')
            self._packet_count = 0
            self._last_log_flush = _time.time()
            self._log_line(f"=== 收包日志开始 {_time.strftime('%Y-%m-%d %H:%M:%S')} "
                           f"目标={self.host}:{self.port} 本机端口={self.socket.getsockname()[1] if self.socket else '?'} ===")

    def _close_packet_log(self):
        """关闭收包日志文件"""
        if self._packet_log_file:
            self._log_line(f"=== 收包日志结束 共收到 {self._packet_count} 个包 ===")
            self._packet_log_file.close()
            self._packet_log_file = None

    def _log_line(self, line: str):
        """写一行到日志文件"""
        if self._packet_log_file:
            self._packet_log_file.write(line + '\n')

    def _log_packet(self, raw_data: bytes):
        """将收到的原始数据包写入日志（含 hex dump）"""
        if not self._packet_log_file:
            return
        import datetime
        self._packet_count += 1
        ts = datetime.datetime.now().strftime('%H:%M:%S.%f')[:-3]
        total = len(raw_data)

        if total >= 12:
            code, param_size, msg_type = struct.unpack('<III', raw_data[:12])
            self._log_line(f"[{ts}] #{self._packet_count} total={total}B "
                           f"code=0x{code:08X} type={msg_type} param_size={param_size}")
        else:
            self._log_line(f"[{ts}] #{self._packet_count} total={total}B "
                           f"(不足12字节，无法解析头部)")
            hex_str = ' '.join(f'{b:02X}' for b in raw_data)
            self._log_line(f"  raw: {hex_str}")
            return

        # hex dump：每行 16 字节，最多 dump 前 256 字节
        dump_len = min(total, 256)
        for offset in range(0, dump_len, 16):
            chunk = raw_data[offset:offset + 16]
            hex_part = ' '.join(f'{b:02X}' for b in chunk[:8])
            if len(chunk) > 8:
                hex_part += '  ' + ' '.join(f'{b:02X}' for b in chunk[8:])
            ascii_part = ''.join(chr(b) if 32 <= b < 127 else '.' for b in chunk)
            self._log_line(f"  {offset:04X}: {hex_part:<50s} {ascii_part}")
        if total > 256:
            self._log_line(f"  ... (截断，共 {total} 字节)")

        # 定期刷新到磁盘
        now = _time.time()
        if now - self._last_log_flush > 2.0:
            self._packet_log_file.flush()
            self._last_log_flush = now

    # =========================================================================
    # 连接管理
    # =========================================================================

    def connect(self, verify: bool = True) -> bool:
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.socket.bind(('0.0.0.0', self.local_port))
            self._open_packet_log()

            if not verify:
                self.socket.settimeout(0.02)  # 接收循环用短超时
                return True

            # 发送心跳包验证连接
            self.socket.settimeout(self.timeout)
            heartbeat = CommandHead(code=0x21040001, parameters_size=0, type=0)
            self.socket.sendto(heartbeat.pack(), (self.host, self.port))

            try:
                data, addr = self.socket.recvfrom(4096)
                print(f"✅ 收到响应，目标主机可达（来自 {addr[0]}:{addr[1]}）")
                # 将验证响应记录到日志，并分发给对应的处理器（不浪费首条数据）
                self._log_packet(data)
                if len(data) >= 12:
                    code, _, _ = struct.unpack('<III', data[:12])
                    print(f"   收到首包指令码: 0x{code:08X}")
                self._dispatch_message(data, silent=True)
            except socket.timeout:
                print(f"⚠️  未收到响应（超时{self.timeout}秒）")
                print(f"   可能原因：")
                print(f"   1. 机器狗未开机或网络不通")
                print(f"   2. 机器狗开机但未配置数据上报到本机")
                print(f"   3. 本机防火墙拦截了机器人回包")
                print(f"   4. 如确定网络可达，可尝试 connect(verify=False) 跳过验证")
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
        self._close_packet_log()

    # =========================================================================
    # 发送
    # =========================================================================

    def send_simple_command(self, code: int, parameters_size: int = 0) -> bool:
        """发送简单指令"""
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
        """发送复杂指令"""
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

    # =========================================================================
    # 消息处理器注册
    # =========================================================================

    def register_handler(self, code: int, handler: Callable):
        """注册消息处理函数"""
        self.message_handlers[code] = handler

    def unregister_handler(self, code: int):
        """注销消息处理函数"""
        if code in self.message_handlers:
            del self.message_handlers[code]

    # =========================================================================
    # 内部：消息分发
    # =========================================================================

    def _dispatch_message(self, raw_data: bytes, silent: bool = False):
        """将接收到的原始数据分发给对应的消息处理器。"""
        if len(raw_data) < 12:
            return
        code, parameters_size, msg_type = struct.unpack('<III', raw_data[:12])
        if msg_type == 1 and len(raw_data) >= 12 + parameters_size:
            message_data = raw_data[12:12 + parameters_size]
        else:
            message_data = b''
        if code in self.message_handlers:
            try:
                self.message_handlers[code](code, message_data)
            except Exception as e:
                if not silent:
                    print(f"处理消息失败: code=0x{code:08X}, error={e}")

    # =========================================================================
    # 接收线程
    # =========================================================================

    def _receive_loop(self):
        """接收消息循环"""
        while self.is_receiving and self.socket:
            try:
                data, addr = self.socket.recvfrom(4096)
                self._log_packet(data)
                if len(data) < 12:  # 至少需要12字节的头部
                    continue
                self._dispatch_message(data)

            except socket.timeout:
                continue
            except Exception as e:
                if self.is_receiving:
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

    # =========================================================================
    # 单次接收（阻塞，调试用）
    # =========================================================================

    def receive_once(self, timeout: Optional[float] = None) -> Optional[Tuple[int, bytes]]:
        """接收一次消息（阻塞）"""
        if not self.socket:
            return None

        old_timeout = self.socket.gettimeout()
        if timeout is not None:
            self.socket.settimeout(timeout)

        try:
            data, addr = self.socket.recvfrom(4096)
            self._log_packet(data)
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
