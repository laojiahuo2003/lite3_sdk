"""机器人状态数据模型"""
from dataclasses import dataclass
from typing import List
from enum import IntEnum


class RobotBasicState(IntEnum):
    """机器人基本运动状态"""
    IDLE = 0  # 空闲/未初始化（固件版本差异）
    LIE_DOWN = 1  # 趴下状态
    PREPARE_STAND = 4  # 准备起立状态
    STANDING_UP = 5  # 正在起立状态
    FORCE_CONTROL = 6  # 力控状态
    LYING_DOWN = 7  # 正在趴下状态
    OUT_OF_CONTROL = 8  # 失控保护状态
    POSTURE_ADJUST = 9  # 姿态调整状态
    ROLLING_OVER = 11  # 执行翻身动作
    AI_STATE = 16  # AI状态
    ZEROING = 17  # 回零状态
    BACKFLIP = 18  # 执行后空翻动作
    GREETING = 20  # 执行打招呼动作


class RobotGaitState(IntEnum):
    """机器人步态"""
    LOW_SPEED = 0  # 平地低速步态
    GENERAL_OBSTACLE = 2  # 通用越障步态
    MEDIUM_SPEED = 4  # 平地中速步态
    HIGH_SPEED = 5  # 平地高速步态
    GRIP_OBSTACLE = 6  # 抓地越障步态
    HIGH_STEP_OBSTACLE = 13  # 高踏步越障步态
    SPACE_WALK = 12  # 太空步步态


class RobotPolicyState(IntEnum):
    """机器人AI步态"""
    AI_BASIC = 0  # AI基础步态
    AI_JUMP = 16  # AI跳跃步态
    AI_STAND = 18  # AI站立步态
    AI_HIGH_SPEED = 20  # AI极速步态


class RobotMotionState(IntEnum):
    """机器人动作状态"""
    IN_BASIC_STATE = 0  # 机器人处于robot_basic_state的值对应的状态中
    TROTTING = 1  # 机器人正在以robot_gait_state的值对应的步态踏步/机器人正处于robot_policy_state的值对应的A步态
    TWISTING_BODY = 2  # 机器人正在执行扭身体
    TWIST_JUMPING = 4  # 机器人正在执行扭身跳
    JUMPING_FORWARD = 11  # 机器人正在执行向前跳


@dataclass
class RobotState:
    """机器人状态信息"""
    version: int  # 固件版本/序列号
    robot_basic_state: int  # 机器人基本运动状态
    robot_gait_state: int  # 机器人当前步态
    robot_policy_state: int  # 机器人当前AI步态
    roll: float  # IMU在世界坐标系下的roll角(°)
    pitch: float  # IMU在世界坐标系下的pitch角(°)
    yaw: float  # IMU在世界坐标系下的yaw角(°)
    roll_vel: float  # IMU在世界坐标系下的roll角速度(rad/s)
    pitch_vel: float  # IMU在世界坐标系下的pitch角速度(rad/s)
    yaw_vel: float  # IMU在世界坐标系下的yaw角速度(rad/s)
    x_acc: float  # IMU在世界坐标系x轴上的加速度(m/s²)
    y_acc: float  # IMU在世界坐标系y轴上的加速度(m/s²)
    z_acc: float  # IMU在世界坐标系z轴上的加速度(m/s²)
    pos_x: float  # 机器人在世界坐标系下的x轴坐标值(m)
    pos_y: float  # 机器人在世界坐标系下的y轴坐标值(m)
    pos_yaw: float  # 机器人在世界坐标系下的yaw角(rad)
    vel_x_world: float  # 机器人在世界坐标系x轴上的速度(m/s)
    vel_y_world: float  # 机器人在世界坐标系y轴上的速度(m/s)
    vel_yaw_world: float  # 机器人在世界坐标系下的yaw角速度(rad/s)
    vel_x_body: float  # 机器人在身体坐标系x轴上的速度(m/s)
    vel_y_body: float  # 机器人在身体坐标系y轴上的速度(m/s)
    vel_yaw_body: float  # 机器人在身体坐标系下的yaw角速度(rad/s)
    touch_down_and_stair_trot: int  # 无效数据，仅作占位用
    is_charging: bool  # 无效数据，仅作占位用
    error_state: int  # 无效数据，仅作占位用
    robot_motion_state: int  # 机器人动作状态
    battery_level: float  # 电池电量百分比的小数形式
    task_state: int  # 无效数据，仅作占位用
    is_robot_need_move: bool  # 机器人受外力影响时的平衡状态
    zero_position_flag: bool  # 回零标志位
    is_after_first_start: bool  # 首次开启标志位
    is_voice_ctrl_enable: bool  # 语音控制功能标志位
    ultrasound_forward: float  # 机器人前方障碍物的距离(m)
    ultrasound_backward: float  # 机器人后方障碍物的距离(m)

    @property
    def basic_state_name(self) -> str:
        """获取基本状态名称"""
        try:
            return RobotBasicState(self.robot_basic_state).name
        except ValueError:
            return f"UNKNOWN({self.robot_basic_state})"

    @property
    def gait_state_name(self) -> str:
        """获取步态名称"""
        try:
            return RobotGaitState(self.robot_gait_state).name
        except ValueError:
            return f"UNKNOWN({self.robot_gait_state})"

    @property
    def policy_state_name(self) -> str:
        """获取AI步态名称"""
        try:
            return RobotPolicyState(self.robot_policy_state).name
        except ValueError:
            return f"UNKNOWN({self.robot_policy_state})"

    @property
    def motion_state_name(self) -> str:
        """获取动作状态名称"""
        try:
            return RobotMotionState(self.robot_motion_state).name
        except ValueError:
            return f"UNKNOWN({self.robot_motion_state})"

    @property
    def is_standing(self) -> bool:
        """机器人是否站立"""
        return self.robot_basic_state in [
            RobotBasicState.FORCE_CONTROL,
            RobotBasicState.AI_STATE
        ]

    @property
    def is_ai_mode(self) -> bool:
        """机器人是否处于AI模式"""
        return self.robot_basic_state == RobotBasicState.AI_STATE

    @property
    def battery_percentage(self) -> float:
        """电池电量百分比

        文档定义为 0~1 小数形式，但部分固件版本直接上报 0~100 的百分比值。
        """
        if self.battery_level > 1.0:
            return self.battery_level  # 固件直接上报百分比
        return self.battery_level * 100.0

    def __str__(self) -> str:
        return (
            f"RobotState(\n"
            f"  基本状态: {self.basic_state_name}\n"
            f"  步态: {self.gait_state_name}\n"
            f"  AI步态: {self.policy_state_name}\n"
            f"  动作状态: {self.motion_state_name}\n"
            f"  电池: {self.battery_percentage:.1f}%\n"
            f"  位置: ({self.pos_x:.2f}, {self.pos_y:.2f}, {self.pos_yaw:.2f}rad)\n"
            f"  速度(世界): ({self.vel_x_world:.2f}, {self.vel_y_world:.2f}, {self.vel_yaw_world:.2f}rad/s)\n"
            f"  速度(身体): ({self.vel_x_body:.2f}, {self.vel_y_body:.2f}, {self.vel_yaw_body:.2f}rad/s)\n"
            f"  姿态: roll={self.roll:.2f}°, pitch={self.pitch:.2f}°, yaw={self.yaw:.2f}°\n"
            f")"
        )