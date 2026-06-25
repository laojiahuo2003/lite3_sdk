"""Lite3 SDK基本测试"""
import unittest
from lite3_sdk import (
    Lite3Client,
    RobotState,
    JointAngles,
    JointVelocities,
    CommandCode,
    HeartbeatCommand,
    RollCommand,
    PitchCommand
)
from lite3_sdk.network import MessageParser
import struct


class TestCommands(unittest.TestCase):
    """测试指令类"""

    def test_heartbeat_command(self):
        """测试心跳指令"""
        cmd = HeartbeatCommand()
        code, size, data = cmd.get_command_data()
        self.assertEqual(code, CommandCode.HEARTBEAT)
        self.assertEqual(size, 0)
        self.assertEqual(data, b'')

    def test_roll_command(self):
        """测试横滚角指令"""
        cmd = RollCommand(10000)
        code, size, data = cmd.get_command_data()
        self.assertEqual(code, CommandCode.AXIS_ROLL)
        self.assertEqual(size, 10000)
        self.assertEqual(data, b'')

    def test_roll_command_limit(self):
        """测试横滚角指令值限制"""
        cmd = RollCommand(40000)  # 超出范围
        code, size, data = cmd.get_command_data()
        self.assertEqual(size, 32767)  # 应被限制到最大值

        cmd = RollCommand(-40000)  # 超出范围
        code, size, data = cmd.get_command_data()
        self.assertEqual(size, -32767)  # 应被限制到最小值


class TestModels(unittest.TestCase):
    """测试数据模型"""

    def test_joint_angles(self):
        """测试关节角度"""
        angles = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.1, 1.2]
        joint_angles = JointAngles(angles)
        self.assertEqual(len(joint_angles.joint_angles), 12)
        self.assertEqual(joint_angles.left_front_abduction, 0.1)
        self.assertEqual(joint_angles.right_hind_knee, 1.2)

    def test_joint_angles_invalid(self):
        """测试关节角度无效数据"""
        with self.assertRaises(ValueError):
            JointAngles([0.1, 0.2, 0.3])  # 只有3个值

    def test_joint_velocities(self):
        """测试关节角速度"""
        velocities = [0.1] * 12
        joint_velocities = JointVelocities(velocities)
        self.assertEqual(len(joint_velocities.joint_velocities), 12)


class TestMessageParser(unittest.TestCase):
    """测试消息解析器"""

    def test_parse_joint_angles(self):
        """测试解析关节角度"""
        # 创建测试数据：12个double值
        angles = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.1, 1.2]
        data = struct.pack('<12d', *angles)

        joint_angles = MessageParser.parse_joint_angles(data)
        self.assertIsNotNone(joint_angles)
        self.assertEqual(len(joint_angles.joint_angles), 12)
        self.assertAlmostEqual(joint_angles.left_front_abduction, 0.1, places=5)

    def test_parse_joint_angles_insufficient_data(self):
        """测试解析关节角度数据不足"""
        data = b'\x00' * 50  # 数据长度不足
        joint_angles = MessageParser.parse_joint_angles(data)
        self.assertIsNone(joint_angles)

    def test_parse_joint_velocities(self):
        """测试解析关节角速度"""
        velocities = [0.5] * 12
        data = struct.pack('<12d', *velocities)

        joint_velocities = MessageParser.parse_joint_velocities(data)
        self.assertIsNotNone(joint_velocities)
        self.assertEqual(len(joint_velocities.joint_velocities), 12)


class TestClient(unittest.TestCase):
    """测试客户端"""

    def test_client_creation(self):
        """测试客户端创建"""
        client = Lite3Client(host="192.168.1.120", port=43893)
        self.assertEqual(client.host, "192.168.1.120")
        self.assertEqual(client.port, 43893)


if __name__ == '__main__':
    unittest.main()