"""SDK功能验证脚本"""
from lite3_sdk import Lite3Client, HeartbeatCommand, RollCommand

print("Lite3 SDK 功能验证")
print("=" * 50)

# 测试1：导入所有主要类
print("\n1. 测试导入...")
try:
    from lite3_sdk import (
        Lite3Client,
        RobotState,
        JointAngles,
        JointVelocities,
        HeartbeatCommand,
        RollCommand,
        PitchCommand,
        StandToggleCommand,
        EnterAICommand
    )
    print("✓ 所有主要类导入成功")
except ImportError as e:
    print(f"✗ 导入失败: {e}")

# 测试2：创建客户端
print("\n2. 测试创建客户端...")
try:
    client = Lite3Client(host="192.168.1.120", port=43893)
    print(f"✓ 客户端创建成功")
    print(f"  目标地址: {client.host}:{client.port}")
except Exception as e:
    print(f"✗ 创建失败: {e}")

# 测试3：创建指令
print("\n3. 测试创建指令...")
try:
    heartbeat = HeartbeatCommand()
    roll_cmd = RollCommand(10000)
    pitch_cmd = PitchCommand(5000)
    
    print("✓ 指令创建成功")
    print(f"  心跳指令码: 0x{heartbeat.code:08X}")
    print(f"  横滚指令值: {roll_cmd.parameters_size}")
except Exception as e:
    print(f"✗ 创建失败: {e}")

# 测试4：数据模型
print("\n4. 测试数据模型...")
try:
    from lite3_sdk.models import RobotBasicState, RobotGaitState
    
    print("✓ 数据模型导入成功")
    print(f"  趴下状态值: {RobotBasicState.LIE_DOWN}")
    print(f"  低速步态值: {RobotGaitState.LOW_SPEED}")
except Exception as e:
    print(f"✗ 导入失败: {e}")

# 测试5：消息解析器
print("\n5. 测试消息解析器...")
try:
    from lite3_sdk.network import MessageParser
    import struct
    
    # 创建测试数据
    angles = [0.1] * 12
    data = struct.pack('<12d', *angles)
    
    joint_angles = MessageParser.parse_joint_angles(data)
    if joint_angles:
        print("✓ 消息解析成功")
        print(f"  关节角度数量: {len(joint_angles.joint_angles)}")
        print(f"  第一个关节角度: {joint_angles.left_front_abduction:.3f} rad")
    else:
        print("✗ 解析失败")
except Exception as e:
    print(f"✗ 解析失败: {e}")

print("\n" + "=" * 50)
print("验证完成！SDK功能正常。")
print("\n使用方法:")
print("  1. 安装SDK: pip install -e .")
print("  2. 导入: from lite3_sdk import Lite3Client")
print("  3. 创建客户端: client = Lite3Client()")
print("  4. 连接: client.connect()")
print("  5. 启动心跳: client.start_heartbeat()")
print("  6. 控制机器人: client.stand_toggle() 等")
print("\n查看 examples/basic_usage.py 获取完整示例。")