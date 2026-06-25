"""指令模块"""

from .base import BaseCommand, SimpleCommand, ComplexCommand
from .command_codes import (
    CommandCode,
    VoiceCommandValue,
    AISettingsValue,
    AIActionValue,
    ContinuousMotionValue,
    SpeakerValue
)
from .motion import (
    HeartbeatCommand,
    AxisCommand,
    RollCommand,
    PitchCommand,
    HeightCommand,
    YawCommand,
    VelocityCommand,
    YawVelocityCommand,
    XVelocityCommand,
    YVelocityCommand
)
from .state import (
    StandToggleCommand,
    SoftEstopCommand,
    ZeroingCommand,
    EnterAICommand,
    ExitAICommand,
    InPlaceModeCommand,
    MovingModeCommand,
    AutonomousModeCommand,
    ManualModeCommand
)
from .gait_action import (
    LowSpeedGaitCommand,
    MediumSpeedGaitCommand,
    HighSpeedGaitCommand,
    CrawlToggleCommand,
    GripObstacleGaitCommand,
    GeneralObstacleGaitCommand,
    HighStepObstacleGaitCommand,
    TwistBodyCommand,
    RollOverCommand,
    SpaceWalkCommand,
    BackflipCommand,
    GreetingCommand,
    JumpForwardCommand,
    TwistJumpCommand,
    StopActionCommand,
    VoiceCommand,
    SpeakerCommand,
    AISettingsCommand,
    ContinuousMotionCommand,
    AIBasicGaitCommand,
    AIJumpGaitCommand,
    AIStandGaitCommand,
    AIHighSpeedGaitCommand,
    AIActionCommand,
    SaveDataCommand
)

__all__ = [
    # 基础类
    'BaseCommand',
    'SimpleCommand',
    'ComplexCommand',

    # 指令码和值枚举
    'CommandCode',
    'VoiceCommandValue',
    'AISettingsValue',
    'AIActionValue',
    'ContinuousMotionValue',
    'SpeakerValue',

    # 运动控制指令
    'HeartbeatCommand',
    'AxisCommand',
    'RollCommand',
    'PitchCommand',
    'HeightCommand',
    'YawCommand',
    'VelocityCommand',
    'YawVelocityCommand',
    'XVelocityCommand',
    'YVelocityCommand',

    # 状态转换指令
    'StandToggleCommand',
    'SoftEstopCommand',
    'ZeroingCommand',
    'EnterAICommand',
    'ExitAICommand',
    'InPlaceModeCommand',
    'MovingModeCommand',
    'AutonomousModeCommand',
    'ManualModeCommand',

    # 步态和动作指令
    'LowSpeedGaitCommand',
    'MediumSpeedGaitCommand',
    'HighSpeedGaitCommand',
    'CrawlToggleCommand',
    'GripObstacleGaitCommand',
    'GeneralObstacleGaitCommand',
    'HighStepObstacleGaitCommand',
    'TwistBodyCommand',
    'RollOverCommand',
    'SpaceWalkCommand',
    'BackflipCommand',
    'GreetingCommand',
    'JumpForwardCommand',
    'TwistJumpCommand',
    'StopActionCommand',
    'VoiceCommand',
    'SpeakerCommand',
    'AISettingsCommand',
    'ContinuousMotionCommand',
    'AIBasicGaitCommand',
    'AIJumpGaitCommand',
    'AIStandGaitCommand',
    'AIHighSpeedGaitCommand',
    'AIActionCommand',
    'SaveDataCommand',
]