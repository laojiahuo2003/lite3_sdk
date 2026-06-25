"""状态转换指令"""
from .base import SimpleCommand
from .command_codes import CommandCode


class StandToggleCommand(SimpleCommand):
    """起立/趴下指令"""

    def __init__(self):
        super().__init__(CommandCode.STAND_TOGGLE)


class SoftEstopCommand(SimpleCommand):
    """软急停指令"""

    def __init__(self):
        super().__init__(CommandCode.SOFT_ESTOP)


class ZeroingCommand(SimpleCommand):
    """回零指令"""

    def __init__(self):
        super().__init__(CommandCode.ZEROING)


class EnterAICommand(SimpleCommand):
    """进入AI指令"""

    def __init__(self):
        super().__init__(CommandCode.ENTER_AI)


class ExitAICommand(SimpleCommand):
    """退出AI指令"""

    def __init__(self):
        super().__init__(CommandCode.EXIT_AI)


class InPlaceModeCommand(SimpleCommand):
    """原地模式指令"""

    def __init__(self):
        super().__init__(CommandCode.MODE_IN_PLACE)


class MovingModeCommand(SimpleCommand):
    """移动模式指令"""

    def __init__(self):
        super().__init__(CommandCode.MODE_MOVING)


class AutonomousModeCommand(SimpleCommand):
    """自主模式指令"""

    def __init__(self):
        super().__init__(CommandCode.CONTROL_AUTONOMOUS)


class ManualModeCommand(SimpleCommand):
    """手动模式指令"""

    def __init__(self):
        super().__init__(CommandCode.CONTROL_MANUAL)