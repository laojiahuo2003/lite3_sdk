"""消息解析器"""
import struct
from typing import Optional
from ..models import RobotState, JointAngles, JointVelocities


class MessageParser:
    """消息解析器"""

    # 机器人固件实际结构体布局 (200字节):
    #   uint32 version;           // 4B  固件版本/序列号
    #   uint8  robot_basic_state;  // 1B  状态字段为单字节
    #   uint8  robot_gait_state;   // 1B
    #   uint8  robot_policy_state; // 1B
    #   uint8  _pad;              // 1B  补齐至 8 字节对齐
    #   double rpy[3];           // 24B  (offset 8, 8-byte aligned)
    #   double rpy_vel[3];       // 24B
    #   double xyz_acc[3];       // 24B
    #   double pos_world[3];     // 24B
    #   double vel_world[3];     // 24B
    #   double vel_body[3];      // 24B
    #   unsigned touch_down_and_stair_trot; // 4B
    #   bool is_charging;          // 1B
    #   uint8 _pad2[3];           // 3B
    #   unsigned error_state;     // 4B
    #   int robot_motion_state;   // 4B
    #   double battery_level;     // 8B
    #   int task_state;           // 4B
    #   bool is_robot_need_move;  // 1B
    #   bool zero_position_flag;  // 1B
    #   bool is_after_first_start;// 1B
    #   bool is_voice_ctrl_enable;// 1B
    #   double ultrasound[2];     // 16B
    # Total: 200 bytes
    _ROBOT_STATE_FORMAT = '<I3Bx18dI?3xIidi4?2d'
    _ROBOT_STATE_SIZE = struct.calcsize(_ROBOT_STATE_FORMAT)  # 200

    @staticmethod
    def parse_robot_state(data: bytes) -> Optional[RobotState]:
        if len(data) < MessageParser._ROBOT_STATE_SIZE:
            return None

        try:
            fields = struct.unpack(MessageParser._ROBOT_STATE_FORMAT,
                                   data[:MessageParser._ROBOT_STATE_SIZE])

            return RobotState(
                version=fields[0],
                robot_basic_state=fields[1],
                robot_gait_state=fields[2],
                robot_policy_state=fields[3],
                roll=fields[4], pitch=fields[5], yaw=fields[6],
                roll_vel=fields[7], pitch_vel=fields[8], yaw_vel=fields[9],
                x_acc=fields[10], y_acc=fields[11], z_acc=fields[12],
                pos_x=fields[13], pos_y=fields[14], pos_yaw=fields[15],
                vel_x_world=fields[16], vel_y_world=fields[17], vel_yaw_world=fields[18],
                vel_x_body=fields[19], vel_y_body=fields[20], vel_yaw_body=fields[21],
                touch_down_and_stair_trot=fields[22],
                is_charging=fields[23],
                error_state=fields[24],
                robot_motion_state=fields[25],
                battery_level=fields[26],
                task_state=fields[27],
                is_robot_need_move=fields[28],
                zero_position_flag=fields[29],
                is_after_first_start=fields[30],
                is_voice_ctrl_enable=fields[31],
                ultrasound_forward=fields[32],
                ultrasound_backward=fields[33],
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
