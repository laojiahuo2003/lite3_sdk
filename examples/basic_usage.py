"""Lite3 SDK使用示例"""
import time
from lite3_sdk import Lite3Client, RobotState, JointAngles, JointVelocities


def robot_state_callback(state: RobotState):
    """机器人状态回调函数"""
    print(f"\n机器人状态更新:")
    print(state)


def joint_angles_callback(angles: JointAngles):
    """关节角度回调函数"""
    print(f"\n关节角度更新:")
    print(angles)


def example_basic_control():
    """基础控制示例"""
    print("=== 基础控制示例 ===")

    # 创建客户端
    client = Lite3Client(host="192.168.1.120", port=43893)

    # 连接
    if not client.connect():
        print("连接失败")
        return

    print("连接成功")

    # 启动心跳
    client.start_heartbeat(rate=5.0)
    print("心跳已启动")

    # 设置回调函数
    client.set_robot_state_callback(robot_state_callback)
    client.set_joint_angles_callback(joint_angles_callback)

    try:
        # 等待接收数据
        print("\n等待接收机器人状态数据...")
        time.sleep(2)

        # 获取当前状态
        if client.robot_state:
            print(f"\n当前机器人状态:")
            print(client.robot_state)

        # 示例：让机器人起立
        print("\n发送起立指令...")
        client.stand_toggle()
        time.sleep(3)

        # 示例：切换到移动模式
        print("\n切换到移动模式...")
        client.set_moving_mode()
        time.sleep(1)

        # 示例：设置低速步态
        print("\n设置低速步态...")
        client.set_low_speed_gait()
        time.sleep(1)

        # 示例：控制机器人前进
        print("\n控制机器人前进...")
        for i in range(10):
            client.set_pitch(10000)  # 向前
            time.sleep(0.05)  # 20Hz频率

        # 停止运动
        print("\n停止运动...")
        client.set_pitch(0)
        client.set_roll(0)
        client.set_yaw(0)
        time.sleep(1)

        # 示例：切换到原地模式
        print("\n切换到原地模式...")
        client.set_in_place_mode()
        time.sleep(1)

        # 示例：调整机器人姿态
        print("\n调整机器人姿态...")
        client.set_pitch(5000)  # 低头
        time.sleep(2)
        client.set_pitch(0)  # 恢复
        time.sleep(1)

    finally:
        # 断开连接
        print("\n断开连接...")
        client.disconnect()
        print("示例完成")


def example_ai_mode():
    """AI模式示例"""
    print("\n=== AI模式示例 ===")

    with Lite3Client(host="192.168.1.120", port=43893) as client:
        # 启动心跳
        client.start_heartbeat()

        print("等待机器人准备...")
        time.sleep(2)

        # 进入AI模式
        print("\n进入AI模式...")
        client.enter_ai()
        time.sleep(2)

        # 设置AI基础步态
        print("\n设置AI基础步态...")
        client.set_ai_basic_gait()
        time.sleep(1)

        # 在AI模式下控制机器人运动
        print("\n在AI模式下控制机器人...")
        for i in range(20):
            client.set_pitch(8000)  # 向前
            client.set_roll(0)
            client.set_yaw(0)
            time.sleep(0.05)

        # 停止运动
        print("\n停止运动...")
        client.set_pitch(0)
        client.set_roll(0)
        client.set_yaw(0)
        time.sleep(1)

        # 退出AI模式
        print("\n退出AI模式...")
        client.exit_ai()
        time.sleep(2)


def example_autonomous_mode():
    """自主模式示例（使用速度指令）"""
    print("\n=== 自主模式示例 ===")

    with Lite3Client(host="192.168.1.120", port=43893) as client:
        # 启动心跳
        client.start_heartbeat()

        print("等待机器人准备...")
        time.sleep(2)

        # 确保机器人站立
        if client.robot_state and not client.robot_state.is_standing:
            print("\n让机器人起立...")
            client.stand_toggle()
            time.sleep(3)

        # 切换到自主模式
        print("\n切换到自主模式...")
        client.set_autonomous_mode()
        time.sleep(1)

        # 使用速度指令控制机器人
        print("\n使用速度指令控制机器人...")
        print("前进 0.5 m/s")
        for i in range(20):
            client.set_x_velocity(0.5)
            time.sleep(0.05)

        print("停止")
        client.set_x_velocity(0.0)
        time.sleep(1)

        print("左转 0.5 rad/s")
        for i in range(20):
            client.set_yaw_velocity(-0.5)
            time.sleep(0.05)

        print("停止")
        client.set_yaw_velocity(0.0)
        time.sleep(1)

        # 切换回手动模式
        print("\n切换回手动模式...")
        client.set_manual_mode()
        time.sleep(1)


def example_actions():
    """动作示例"""
    print("\n=== 动作示例 ===")

    with Lite3Client(host="192.168.1.120", port=43893) as client:
        # 启动心跳
        client.start_heartbeat()

        print("等待机器人准备...")
        time.sleep(2)

        # 确保机器人站立
        if client.robot_state and client.robot_state.is_standing:
            print("\n机器人正在站立，执行扭身体动作...")
            client.twist_body()
            time.sleep(5)

            print("\n停止动作...")
            client.stop_action()
            time.sleep(1)

        # 让机器人趴下
        print("\n让机器人趴下...")
        client.stand_toggle()
        time.sleep(3)

        # 执行翻身动作
        print("\n执行翻身动作...")
        client.roll_over()
        time.sleep(5)

        # 让机器人起立
        print("\n让机器人起立...")
        client.stand_toggle()
        time.sleep(3)


def example_monitoring():
    """监控示例"""
    print("\n=== 监控示例 ===")

    def state_callback(state: RobotState):
        """状态回调"""
        print(f"\n[{time.strftime('%H:%M:%S')}] 状态更新:")
        print(f"  基本状态: {state.basic_state_name}")
        print(f"  步态: {state.gait_state_name}")
        print(f"  电池: {state.battery_percentage:.1f}%")
        print(f"  位置: ({state.pos_x:.2f}, {state.pos_y:.2f})")

    with Lite3Client(host="192.168.1.120", port=43893) as client:
        # 启动心跳
        client.start_heartbeat()

        # 设置回调
        client.set_robot_state_callback(state_callback)

        print("开始监控机器人状态（10秒）...")
        time.sleep(10)

        print("\n监控结束")


if __name__ == "__main__":
    print("Lite3 SDK 使用示例")
    print("=" * 50)

    # 运行示例（根据需要选择）
    try:
        # 基础控制示例
        example_basic_control()

        # AI模式示例
        # example_ai_mode()

        # 自主模式示例
        # example_autonomous_mode()

        # 动作示例
        # example_actions()

        # 监控示例
        # example_monitoring()

    except KeyboardInterrupt:
        print("\n用户中断")
    except Exception as e:
        print(f"\n错误: {e}")