"""机器人关节数据模型"""
from dataclasses import dataclass
from typing import List
import struct


@dataclass
class JointAngles:
    """机器人关节角度信息"""
    joint_angles: List[float]  # 12个关节的角度，单位rad

    def __post_init__(self):
        if len(self.joint_angles) != 12:
            raise ValueError(f"Expected 12 joint angles, got {len(self.joint_angles)}")

    @property
    def left_front_abduction(self) -> float:
        """左前侧摆关节角度"""
        return self.joint_angles[0]

    @property
    def left_front_hip(self) -> float:
        """左前髋关节角度"""
        return self.joint_angles[1]

    @property
    def left_front_knee(self) -> float:
        """左前膝关节角度"""
        return self.joint_angles[2]

    @property
    def right_front_abduction(self) -> float:
        """右前侧摆关节角度"""
        return self.joint_angles[3]

    @property
    def right_front_hip(self) -> float:
        """右前髋关节角度"""
        return self.joint_angles[4]

    @property
    def right_front_knee(self) -> float:
        """右前膝关节角度"""
        return self.joint_angles[5]

    @property
    def left_hind_abduction(self) -> float:
        """左后侧摆关节角度"""
        return self.joint_angles[6]

    @property
    def left_hind_hip(self) -> float:
        """左后髋关节角度"""
        return self.joint_angles[7]

    @property
    def left_hind_knee(self) -> float:
        """左后膝关节角度"""
        return self.joint_angles[8]

    @property
    def right_hind_abduction(self) -> float:
        """右后侧摆关节角度"""
        return self.joint_angles[9]

    @property
    def right_hind_hip(self) -> float:
        """右后髋关节角度"""
        return self.joint_angles[10]

    @property
    def right_hind_knee(self) -> float:
        """右后膝关节角度"""
        return self.joint_angles[11]

    def __str__(self) -> str:
        return (
            f"JointAngles(\n"
            f"  左前: [{self.left_front_abduction:.3f}, {self.left_front_hip:.3f}, {self.left_front_knee:.3f}]\n"
            f"  右前: [{self.right_front_abduction:.3f}, {self.right_front_hip:.3f}, {self.right_front_knee:.3f}]\n"
            f"  左后: [{self.left_hind_abduction:.3f}, {self.left_hind_hip:.3f}, {self.left_hind_knee:.3f}]\n"
            f"  右后: [{self.right_hind_abduction:.3f}, {self.right_hind_hip:.3f}, {self.right_hind_knee:.3f}]\n"
            f")"
        )


@dataclass
class JointVelocities:
    """机器人关节角速度信息"""
    joint_velocities: List[float]  # 12个关节的角速度，单位rad/s

    def __post_init__(self):
        if len(self.joint_velocities) != 12:
            raise ValueError(f"Expected 12 joint velocities, got {len(self.joint_velocities)}")

    @property
    def left_front_abduction(self) -> float:
        """左前侧摆关节角速度"""
        return self.joint_velocities[0]

    @property
    def left_front_hip(self) -> float:
        """左前髋关节角速度"""
        return self.joint_velocities[1]

    @property
    def left_front_knee(self) -> float:
        """左前膝关节角速度"""
        return self.joint_velocities[2]

    @property
    def right_front_abduction(self) -> float:
        """右前侧摆关节角速度"""
        return self.joint_velocities[3]

    @property
    def right_front_hip(self) -> float:
        """右前髋关节角速度"""
        return self.joint_velocities[4]

    @property
    def right_front_knee(self) -> float:
        """右前膝关节角速度"""
        return self.joint_velocities[5]

    @property
    def left_hind_abduction(self) -> float:
        """左后侧摆关节角速度"""
        return self.joint_velocities[6]

    @property
    def left_hind_hip(self) -> float:
        """左后髋关节角速度"""
        return self.joint_velocities[7]

    @property
    def left_hind_knee(self) -> float:
        """左后膝关节角速度"""
        return self.joint_velocities[8]

    @property
    def right_hind_abduction(self) -> float:
        """右后侧摆关节角速度"""
        return self.joint_velocities[9]

    @property
    def right_hind_hip(self) -> float:
        """右后髋关节角速度"""
        return self.joint_velocities[10]

    @property
    def right_hind_knee(self) -> float:
        """右后膝关节角速度"""
        return self.joint_velocities[11]

    def __str__(self) -> str:
        return (
            f"JointVelocities(\n"
            f"  左前: [{self.left_front_abduction:.3f}, {self.left_front_hip:.3f}, {self.left_front_knee:.3f}]\n"
            f"  右前: [{self.right_front_abduction:.3f}, {self.right_front_hip:.3f}, {self.right_front_knee:.3f}]\n"
            f"  左后: [{self.left_hind_abduction:.3f}, {self.left_hind_hip:.3f}, {self.left_hind_knee:.3f}]\n"
            f"  右后: [{self.right_hind_abduction:.3f}, {self.right_hind_hip:.3f}, {self.right_hind_knee:.3f}]\n"
            f")"
        )