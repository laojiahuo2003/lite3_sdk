"""步态和动作指令"""
from .base import SimpleCommand
from .command_codes import (
    CommandCode,
    VoiceCommandValue,
    AISettingsValue,
    AIActionValue,
    ContinuousMotionValue,
    SpeakerValue
)


class GaitCommand(SimpleCommand):
    """步态切换指令基类"""

    def __init__(self, code: int):
        super().__init__(code)


class LowSpeedGaitCommand(GaitCommand):
    """平地低速步态指令"""

    def __init__(self):
        super().__init__(CommandCode.GAIT_LOW_SPEED)


class MediumSpeedGaitCommand(GaitCommand):
    """平地中速步态指令"""

    def __init__(self):
        super().__init__(CommandCode.GAIT_MEDIUM_SPEED)


class HighSpeedGaitCommand(GaitCommand):
    """平地高速步态指令"""

    def __init__(self):
        super().__init__(CommandCode.GAIT_HIGH_SPEED)


class CrawlToggleCommand(GaitCommand):
    """正常/匍匐步态切换指令"""

    def __init__(self):
        super().__init__(CommandCode.GAIT_CRAWL_TOGGLE)


class GripObstacleGaitCommand(GaitCommand):
    """抓地越障步态指令"""

    def __init__(self):
        super().__init__(CommandCode.GAIT_GRIP_OBSTACLE)


class GeneralObstacleGaitCommand(GaitCommand):
    """通用越障步态指令"""

    def __init__(self):
        super().__init__(CommandCode.GAIT_GENERAL_OBSTACLE)


class HighStepObstacleGaitCommand(GaitCommand):
    """高踏步越障步态指令"""

    def __init__(self):
        super().__init__(CommandCode.GAIT_HIGH_STEP_OBSTACLE)


class ActionCommand(SimpleCommand):
    """动作指令基类"""

    def __init__(self, code: int):
        super().__init__(code)


class TwistBodyCommand(ActionCommand):
    """扭身体指令"""

    def __init__(self):
        super().__init__(CommandCode.ACTION_TWIST_BODY)


class RollOverCommand(ActionCommand):
    """翻身指令"""

    def __init__(self):
        super().__init__(CommandCode.ACTION_ROLL_OVER)


class SpaceWalkCommand(ActionCommand):
    """太空步指令"""

    def __init__(self):
        super().__init__(CommandCode.ACTION_SPACE_WALK)


class BackflipCommand(ActionCommand):
    """后空翻指令"""

    def __init__(self):
        super().__init__(CommandCode.ACTION_BACKFLIP)


class GreetingCommand(ActionCommand):
    """打招呼指令"""

    def __init__(self):
        super().__init__(CommandCode.ACTION_GREETING)


class JumpForwardCommand(ActionCommand):
    """向前跳指令"""

    def __init__(self):
        super().__init__(CommandCode.ACTION_JUMP_FORWARD)


class TwistJumpCommand(ActionCommand):
    """扭身跳指令"""

    def __init__(self):
        super().__init__(CommandCode.ACTION_TWIST_JUMP)


class StopActionCommand(SimpleCommand):
    """停止动作指令（文档要求同时发送指令值 0 和 1）"""

    def __init__(self, value: int = 0):
        super().__init__(CommandCode.ACTION_STOP, value)


class VoiceCommand(SimpleCommand):
    """语音指令"""

    def __init__(self, value: VoiceCommandValue):
        """
        初始化语音指令

        Args:
            value: 语音指令值
        """
        super().__init__(CommandCode.VOICE_COMMAND, value)


class SpeakerCommand(SimpleCommand):
    """扬声器指令"""

    def __init__(self, value: SpeakerValue):
        """
        初始化扬声器指令

        Args:
            value: 扬声器指令值
        """
        super().__init__(CommandCode.SPEAKER_CONTROL, value)


class AISettingsCommand(SimpleCommand):
    """AI设置指令"""

    def __init__(self, value: AISettingsValue):
        """
        初始化AI设置指令

        Args:
            value: AI设置值
        """
        super().__init__(CommandCode.AI_SETTINGS, value)


class ContinuousMotionCommand(SimpleCommand):
    """持续运动指令"""

    def __init__(self, enable: bool):
        """
        初始化持续运动指令

        Args:
            enable: True开启，False关闭
        """
        value = ContinuousMotionValue.ENABLE if enable else ContinuousMotionValue.DISABLE
        super().__init__(CommandCode.CONTINUOUS_MOTION, value)


class AIGaitCommand(SimpleCommand):
    """AI步态切换指令基类"""

    def __init__(self, code: int):
        super().__init__(code)


class AIBasicGaitCommand(AIGaitCommand):
    """AI基础步态指令"""

    def __init__(self):
        super().__init__(CommandCode.AI_GAIT_BASIC)


class AIJumpGaitCommand(AIGaitCommand):
    """AI跳跃步态指令"""

    def __init__(self):
        super().__init__(CommandCode.AI_GAIT_JUMP)


class AIStandGaitCommand(AIGaitCommand):
    """AI站立步态指令"""

    def __init__(self):
        super().__init__(CommandCode.AI_GAIT_STAND)


class AIHighSpeedGaitCommand(AIGaitCommand):
    """AI极速步态指令"""

    def __init__(self):
        super().__init__(CommandCode.AI_GAIT_HIGH_SPEED)


class AIActionCommand(SimpleCommand):
    """AI动作指令"""

    def __init__(self, value: AIActionValue):
        """
        初始化AI动作指令

        Args:
            value: AI动作值
        """
        super().__init__(CommandCode.AI_ACTION, value)


class SaveDataCommand(SimpleCommand):
    """保存数据指令"""

    def __init__(self):
        super().__init__(CommandCode.SAVE_DATA)