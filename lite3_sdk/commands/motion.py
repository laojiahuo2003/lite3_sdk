"""运动控制指令"""
import struct
from .base import SimpleCommand, ComplexCommand
from .command_codes import CommandCode


class HeartbeatCommand(SimpleCommand):
    """心跳指令"""

    def __init__(self):
        super().__init__(CommandCode.HEARTBEAT)


class AxisCommand(SimpleCommand):
    """轴指令基类"""

    def __init__(self, code: int, value: int, deadzone: int = 0):
        value = max(-32767, min(32767, value))
        if abs(value) < deadzone:
            value = 0
        super().__init__(code, value)


class RollCommand(AxisCommand):
    """横滚角/左右平移指令（死区 ±12553）"""

    def __init__(self, value: int):
        super().__init__(CommandCode.AXIS_ROLL, value, deadzone=12553)


class PitchCommand(AxisCommand):
    """俯仰角/前后平移指令（死区 ±6553）"""

    def __init__(self, value: int):
        super().__init__(CommandCode.AXIS_PITCH, value, deadzone=6553)


class HeightCommand(AxisCommand):
    """身体高度指令（范围 [-20000, 20000]）"""

    def __init__(self, value: int):
        value = max(-20000, min(20000, value))
        super().__init__(CommandCode.AXIS_HEIGHT, value)


class YawCommand(AxisCommand):
    """偏航角/左右转弯指令（死区 ±9553）"""

    def __init__(self, value: int):
        super().__init__(CommandCode.AXIS_YAW, value, deadzone=9553)


class VelocityCommand(ComplexCommand):
    """速度指令（复杂指令）"""

    def __init__(self, code: int, velocity: float):
        """
        初始化速度指令

        Args:
            code: 指令码
            velocity: 速度值
        """
        # 打包为double类型（小端字节序）
        data = struct.pack('<d', velocity)
        super().__init__(code, data)


class YawVelocityCommand(VelocityCommand):
    """旋转角速度指令"""

    def __init__(self, velocity: float):
        """
        初始化旋转角速度指令

        Args:
            velocity: 旋转角速度(rad/s)，范围[-1.5, 1.5]
        """
        velocity = max(-1.5, min(1.5, velocity))
        super().__init__(CommandCode.VELOCITY_YAW, velocity)


class XVelocityCommand(VelocityCommand):
    """前后平移速度指令"""

    def __init__(self, velocity: float):
        """
        初始化前后平移速度指令

        Args:
            velocity: 前后平移速度(m/s)，范围[-1.0, 1.0]
        """
        velocity = max(-1.0, min(1.0, velocity))
        super().__init__(CommandCode.VELOCITY_X, velocity)


class YVelocityCommand(VelocityCommand):
    """左右平移速度指令"""

    def __init__(self, velocity: float):
        """
        初始化左右平移速度指令

        Args:
            velocity: 左右平移速度(m/s)，范围[-0.5, 0.5]
        """
        velocity = max(-0.5, min(0.5, velocity))
        super().__init__(CommandCode.VELOCITY_Y, velocity)