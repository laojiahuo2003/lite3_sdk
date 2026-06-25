"""指令码定义"""
from enum import IntEnum


class CommandCode(IntEnum):
    """指令码枚举"""

    # 心跳指令
    HEARTBEAT = 0x21040001

    # 机器人基本状态转换指令
    STAND_TOGGLE = 0x21010202  # 起立/趴下
    SOFT_ESTOP = 0x21020C0E  # 软急停
    ZEROING = 0x21010C05  # 回零
    ENTER_AI = 0x21010528  # 进入AI
    EXIT_AI = 0x2101052B  # 退出AI

    # 轴指令
    AXIS_ROLL = 0x21010131  # 调整横滚角/左右平移
    AXIS_PITCH = 0x21010130  # 调整俯仰角/前后平移
    AXIS_HEIGHT = 0x21010102  # 调整身体高度
    AXIS_YAW = 0x21010135  # 调整偏航角/左右转弯

    # 运动模式切换指令
    MODE_IN_PLACE = 0x21010D05  # 原地模式
    MODE_MOVING = 0x21010D06  # 移动模式

    # 步态切换指令
    GAIT_LOW_SPEED = 0x21010300  # 平地低速步态
    GAIT_MEDIUM_SPEED = 0x21010307  # 平地中速步态
    GAIT_HIGH_SPEED = 0x21010303  # 平地高速步态
    GAIT_CRAWL_TOGGLE = 0x21010406  # 正常/匍匐
    GAIT_GRIP_OBSTACLE = 0x21010402  # 抓地越障步态
    GAIT_GENERAL_OBSTACLE = 0x21010401  # 通用越障步态
    GAIT_HIGH_STEP_OBSTACLE = 0x21010407  # 高踏步越障步态

    # 动作指令
    ACTION_TWIST_BODY = 0x21010204  # 扭身体
    ACTION_ROLL_OVER = 0x21010205  # 翻身
    ACTION_SPACE_WALK = 0x2101030C  # 太空步
    ACTION_BACKFLIP = 0x21010502  # 后空翻
    ACTION_GREETING = 0x21010507  # 打招呼
    ACTION_JUMP_FORWARD = 0x2101050B  # 向前跳
    ACTION_TWIST_JUMP = 0x2101020D  # 扭身跳
    ACTION_STOP = 0x21010C0B  # 停止动作

    # 控制模式切换指令
    CONTROL_AUTONOMOUS = 0x21010C03  # 自主模式
    CONTROL_MANUAL = 0x21010C02  # 手动模式

    # 保存数据指令
    SAVE_DATA = 0x21010C01

    # 持续运动指令
    CONTINUOUS_MOTION = 0x21010C06

    # 语音指令
    VOICE_COMMAND = 0x21010C0A

    # 扬声器指令
    SPEAKER_CONTROL = 0x2101030D

    # 感知设置类指令
    AI_SETTINGS = 0x21012109

    # 速度指令（复杂指令）
    VELOCITY_YAW = 0x0141  # 指定旋转角速度
    VELOCITY_X = 0x0140  # 指定前后平移的速度
    VELOCITY_Y = 0x0145  # 指定左右平移的速度

    # AI步态切换指令
    AI_GAIT_BASIC = 0x2101052A  # AI基础步态
    AI_GAIT_JUMP = 0x21010529  # AI跳跃步态
    AI_GAIT_STAND = 0x2101052C  # AI站立步态
    AI_GAIT_HIGH_SPEED = 0x2101052E  # AI极速步态

    # AI动作指令
    AI_ACTION = 0x2101030E

    # 接收信息指令码
    RECV_ROBOT_STATE = 0x0901  # 机器人状态信息
    RECV_JOINT_ANGLE = 0x0902  # 关节角度信息
    RECV_JOINT_VELOCITY = 0x0903  # 关节角速度信息
    RECV_SPEAKER_STATE = 0x11050f08  # 扬声器状态


class VoiceCommandValue(IntEnum):
    """语音指令值"""
    STOP = 0  # 停止语音指令
    STAND_UP = 1  # 起立
    SIT_DOWN = 2  # 坐下
    FORWARD = 3  # 前进
    BACKWARD = 4  # 后退
    LEFT = 5  # 向左平移
    RIGHT = 6  # 向右平移
    STOP_MOTION = 7  # 停止
    LOOK_DOWN = 8  # 低头
    LOOK_UP = 9  # 抬头
    LOOK_LEFT = 11  # 向左看
    LOOK_RIGHT = 12  # 向右看
    TURN_LEFT_90 = 13  # 向左转90°
    TURN_RIGHT_90 = 14  # 向右转90°
    TURN_BACK_180 = 15  # 向后转180°
    GREETING = 22  # 打招呼


class AISettingsValue(IntEnum):
    """AI设置值"""
    DISABLE_ALL = 0x00  # 关闭所有AI选项功能
    ENABLE_OBSTACLE_AVOIDANCE = 0x20  # 开启停障
    ENABLE_FOLLOWING = 0xC0  # 开启跟随
    ENABLE_NAVIGATION = 0x40  # 开启导航避障


class AIActionValue(IntEnum):
    """AI动作值"""
    HANDSTAND = 4  # 倒立
    BACKFLIP = 64  # 原地空翻
    JUMP = 128  # 原地跳跃
    STOP = 0  # 停止表演AI动作


class ContinuousMotionValue(IntEnum):
    """持续运动值"""
    ENABLE = 1  # 开启
    DISABLE = 2  # 关闭


class SpeakerValue(IntEnum):
    """扬声器值"""
    OFF = 0  # 关闭扬声器
    ON = 1  # 打开扬声器
    QUERY = 2  # 查询扬声器状态