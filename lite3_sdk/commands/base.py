"""基础指令类"""
from abc import ABC, abstractmethod
from typing import Tuple


class BaseCommand(ABC):
    """基础指令抽象类"""

    @abstractmethod
    def get_command_data(self) -> Tuple[int, int, bytes]:
        """
        获取指令数据

        Returns:
            (指令码, 参数大小, 数据)
        """
        pass


class SimpleCommand(BaseCommand):
    """简单指令"""

    def __init__(self, code: int, parameters_size: int = 0):
        """
        初始化简单指令

        Args:
            code: 指令码
            parameters_size: 参数大小（通常为0）
        """
        self.code = code
        self.parameters_size = parameters_size

    def get_command_data(self) -> Tuple[int, int, bytes]:
        return (self.code, self.parameters_size, b'')


class ComplexCommand(BaseCommand):
    """复杂指令"""

    def __init__(self, code: int, data: bytes):
        """
        初始化复杂指令

        Args:
            code: 指令码
            data: 数据内容
        """
        self.code = code
        self.data = data

    def get_command_data(self) -> Tuple[int, int, bytes]:
        return (self.code, len(self.data), self.data)