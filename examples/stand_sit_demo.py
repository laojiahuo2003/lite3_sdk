"""Lite3机器人起立和趴下示例"""
import time
from lite3_sdk import Lite3Client
from lite3_sdk.models import RobotBasicState


def wait_for_state(client: Lite3Client, target_states: list, timeout: float = 15.0, check_interval: float = 0.05) -> bool:
    """
    等待机器人状态变化到目标状态

    Args:
        client: Lite3客户端
        target_states: 目标状态列表（RobotBasicState枚举值）
        timeout: 超时时间（秒）
        check_interval: 检查间隔（秒）

    Returns:
        是否成功到达目标状态
    """
    start_time = time.time()
    last_state = None

    while time.time() - start_time < timeout:
        if client.robot_state:
            current_state = client.robot_state.robot_basic_state

            # 状态变化时打印
            if current_state != last_state:
                print(f"  状态变化: {client.robot_state.basic_state_name}")
                last_state = current_state

            # 检查是否到达目标状态
            if current_state in target_states:
                return True

        time.sleep(check_interval)

    return False


def main():
    """起立和趴下演示"""
    print("Lite3机器人起立/趴下示例")
    print("=" * 50)

    # 创建客户端（修改为你的机器人IP）
    client = Lite3Client(host="192.168.2.1", port=43893)

    # 连接机器人
    # 注意：verify=True会验证目标主机是否可达
    # 如果机器狗未开机，连接会失败
    # 如果不确定机器狗状态，可以使用 verify=False
    print("\n正在连接机器人...")
    if not client.connect(verify=True):
        print("❌ 连接失败！")
        print("   请检查：")
        print("   1. 机器狗是否已开机")
        print("   2. 网络连接是否正常")
        print("   3. IP地址是否正确")
        print("   4. 是否已配置数据上报（参考运动主机通讯接口.txt第4节）")
        print("\n提示：如果不确定机器狗状态，可以使用 verify=False 参数")
        return

    print("✅ 连接成功")

    # 启动心跳（必须，频率不低于2Hz）
    print("\n启动心跳...")
    client.start_heartbeat(rate=5.0)  # 5Hz
    print("✅ 心跳已启动")

    try:
        # 等待接收机器人状态
        print("\n等待接收机器人状态数据...")
        time.sleep(2)

        # 显示当前状态
        if client.robot_state:
            print(f"\n当前机器人状态:")
            print(f"  基本状态: {client.robot_state.basic_state_name}")
            print(f"  电池电量: {client.robot_state.battery_percentage:.1f}%")
        else:
            print("⚠️  未接收到状态数据")

        # 第一次：让机器人起立
        print("\n" + "=" * 50)
        print("操作1: 发送起立指令")
        print("=" * 50)
        client.stand_toggle()
        print("✅ 已发送起立指令")

        # 等待机器人完成起立动作
        # 起立过程：趴下(1) -> 准备起立(4) -> 正在起立(5) -> 力控状态(6)
        print("\n等待机器人起立...")
        if wait_for_state(client, [RobotBasicState.FORCE_CONTROL], timeout=15.0):
            print("✅ 起立完成！")
        else:
            print("⚠️  起立超时，请检查机器人状态")

        # 显示状态
        if client.robot_state:
            print(f"\n当前状态: {client.robot_state.basic_state_name}")
            print(f"电池电量: {client.robot_state.battery_percentage:.1f}%")

        # 第二次：让机器人趴下
        print("\n" + "=" * 50)
        print("操作2: 发送趴下指令")
        print("=" * 50)
        client.stand_toggle()
        print("✅ 已发送趴下指令")

        # 等待机器人完成趴下动作
        # 趴下过程：站立(6) -> 正在趴下(7) -> 趴下(1)
        print("\n等待机器人趴下...")
        if wait_for_state(client, [RobotBasicState.LIE_DOWN], timeout=10.0):
            print("✅ 趴下完成！")
        else:
            print("⚠️  趴下超时，请检查机器人状态")

        # 显示状态
        if client.robot_state:
            print(f"\n当前状态: {client.robot_state.basic_state_name}")
            print(f"电池电量: {client.robot_state.battery_percentage:.1f}%")

        print("\n" + "=" * 50)
        print("演示完成！")
        print("=" * 50)

    except KeyboardInterrupt:
        print("\n\n用户中断操作")

    finally:
        # 断开连接
        print("\n正在断开连接...")
        client.disconnect()
        print("✅ 已断开连接")


if __name__ == "__main__":
    # 使用说明
    print("\n使用说明:")
    print("1. 确保机器人已开机并连接到网络")
    print("2. 修改 host 参数为你的机器人IP地址")
    print("3. 运行此脚本: python stand_sit_demo.py")
    print("4. 观察机器人执行起立和趴下动作")
    print("\n注意:")
    print("- stand_toggle() 方法会在起立和趴下之间切换")
    print("- 每次动作需要等待约5秒完成")
    print("- 确保机器人有足够的电池电量")
    print("\n")

    # 运行主程序
    main()