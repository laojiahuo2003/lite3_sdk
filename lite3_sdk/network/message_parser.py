"""消息解析器"""
import struct
from typing import Optional
from ..models import RobotState, JointAngles, JointVelocities


class MessageParser:
    """消息解析器"""

    # RobotStateUpload C 结构体对齐布局（标准 ABI，double 对齐 8 字节）
    # int(4)+int(4)+int(4)+[pad4]+double*18+unsigned(4)+bool(1)+[pad3]+unsigned(4)+int(4)
    # +double(8)+int(4)+bool*4+double*2 = 208 bytes
    _ROBOT_STATE_FORMAT = '<3i4x18dI?3xIid4?2d'
    _ROBOT_STATE_SIZE = struct.calcsize(_ROBOT_STATE_FORMAT)  # 208

    @staticmethod
    def parse_robot_state(data: bytes) -> Optional[RobotState]:
        if len(data) < MessageParser._ROBOT_STATE_SIZE:
            return None

        try:
            fields = struct.unpack(MessageParser._ROBOT_STATE_FORMAT, data[:MessageParser._ROBOT_STATE_SIZE])

            return RobotState(
                robot_basic_state=fields[0],
                robot_gait_state=fields[1],
                robot_policy_state=fields[2],
                roll=fields[3], pitch=fields[4], yaw=fields[5],
                roll_vel=fields[6], pitch_vel=fields[7], yaw_vel=fields[8],
                x_acc=fields[9], y_acc=fields[10], z_acc=fields[11],
                pos_x=fields[12], pos_y=fields[13], pos_yaw=fields[14],
                vel_x_world=fields[15], vel_y_world=fields[16], vel_yaw_world=fields[17],
                vel_x_body=fields[18], vel_y_body=fields[19], vel_yaw_body=fields[20],
                touch_down_and_stair_trot=fields[21],
                is_charging=fields[22],
                error_state=fields[23],
                robot_motion_state=fields[24],
                battery_level=fields[25],
                task_state=fields[26],
                is_robot_need_move=fields[27],
                zero_position_flag=fields[28],
                is_after_first_start=fields[29],
                is_voice_ctrl_enable=fields[30],
                ultrasound_forward=fields[31],
                ultrasound_backward=fields[32],
            )
        except Exception as e:
            print(f"解析机器人状态失败: {e}")
            return None

    @staticmethod
    def parse_joint_angles(data: bytes) -> Optional[JointAngles]:
        if len(data) < 96:
            return None
        try:
            joint_angles = list(struct.unpack('<12d', data[:96]))
            return JointAngles(joint_angles=joint_angles)
        except Exception as e:
            print(f"解析关节角度失败: {e}")
            return None

    @staticmethod
    def parse_joint_velocities(data: bytes) -> Optional[JointVelocities]:
        if len(data) < 96:
            return None
        try:
            joint_velocities = list(struct.unpack('<12d', data[:96]))
            return JointVelocities(joint_velocities=joint_velocities)
        except Exception as e:
            print(f"解析关节角速度失败: {e}")
            return None
