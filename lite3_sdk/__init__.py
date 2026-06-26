"""Lite3机器人SDK"""

from .client import Lite3Client
from .camera_client import CameraClient
from .models import (
    RobotState,
    RobotBasicState,
    RobotGaitState,
    RobotPolicyState,
    RobotMotionState,
    JointAngles,
    JointVelocities
)
from .commands import (
    BaseCommand,
    SimpleCommand,
    ComplexCommand,
    CommandCode,
    VoiceCommandValue,
    AISettingsValue,
    AIActionValue,
    ContinuousMotionValue,
    SpeakerValue,
    HeartbeatCommand,
    RollCommand,
    PitchCommand,
    HeightCommand,
    YawCommand,
    YawVelocityCommand,
    XVelocityCommand,
    YVelocityCommand,
    StandToggleCommand,
    SoftEstopCommand,
    ZeroingCommand,
    EnterAICommand,
    ExitAICommand,
    InPlaceModeCommand,
    MovingModeCommand,
    AutonomousModeCommand,
    ManualModeCommand,
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

__version__ = "1.0.0"

__all__ = [
    # 主客户端
    'Lite3Client',
    'CameraClient',

    # 数据模型
    'RobotState',
    'RobotBasicState',
    'RobotGaitState',
    'RobotPolicyState',
    'RobotMotionState',
    'JointAngles',
    'JointVelocities',

    # 指令基类
    'BaseCommand',
    'SimpleCommand',
    'ComplexCommand',

    # 枚举
    'CommandCode',
    'VoiceCommandValue',
    'AISettingsValue',
    'AIActionValue',
    'ContinuousMotionValue',
    'SpeakerValue',

    # 运动控制指令
    'HeartbeatCommand',
    'RollCommand',
    'PitchCommand',
    'HeightCommand',
    'YawCommand',
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