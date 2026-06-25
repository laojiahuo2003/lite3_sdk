"""测试Lite3机器人连接"""
import time
from lite3_sdk import Lite3Client


def test_connection():
    """测试连接"""
    print("Lite3机器人连接测试")
    print("=" * 50)

    # 创建客户端
    client = Lite3Client(host="192.168.1.120", port=43893, timeout=2.0)

    print("\n测试1: 验证连接（verify=True）")
    print("-" * 50)
    print("正在连接并验证目标主机...")

    if client.connect(verify=True):
        print("✅ 连接成功！机器狗已开机并可达")
        client.disconnect()
    else:
        print("❌ 连接失败")
        print("\n可能原因：")
        print("1. 机器狗未开机")
        print("2. 网络不通（ping测试失败）")
        print("3. IP地址错误")
        print("4. 未配置数据上报")

    print("\n测试2: 不验证连接（verify=False）")
    print("-" * 50)
    print("创建socket但不验证...")

    if client.connect(verify=False):
        print("✅ Socket创建成功（但未验证目标可达性）")
        print("\n发送心跳包测试...")
        client.start_heartbeat(rate=2.0)

        # 等待5秒看是否收到数据
        print("等待5秒观察是否收到数据...")
        time.sleep(5)

        if client.robot_state:
            print("✅ 收到机器人状态数据！")
            print(f"   状态: {client.robot_state.basic_state_name}")
            print(f"   电池: {client.robot_state.battery_percentage:.1f}%")
        else:
            print("⚠️  未收到数据")
            print("   可能机器狗未开机或未配置数据上报")

        client.disconnect()
    else:
        print("❌ Socket创建失败")


def ping_test():
    """ping测试"""
    import subprocess
    import platform

    print("\n网络连通性测试")
    print("=" * 50)

    host = "192.168.1.120"
    print(f"正在ping {host}...")

    # 执行ping命令
    try:
        # Windows使用 -n，Linux/macOS使用 -c
        param = '-n' if platform.system().lower() == 'windows' else '-c'
        command = ['ping', param, '3', host]

        result = subprocess.run(command, capture_output=True, text=True, timeout=10)

        if result.returncode == 0:
            print("✅ Ping成功！目标主机可达")
            print("\nPing结果:")
            print(result.stdout)
        else:
            print("❌ Ping失败！目标主机不可达")
            print("\n错误信息:")
            print(result.stdout)
            print(result.stderr)

    except subprocess.TimeoutExpired:
        print("❌ Ping超时")
    except Exception as e:
        print(f"❌ Ping测试失败: {e}")


if __name__ == "__main__":
    print("\n使用说明:")
    print("1. 确保机器狗已开机")
    print("2. 确保网络连接正常")
    print("3. 修改 host 参数为你的机器狗IP")
    print("\n")

    # 运行ping测试
    ping_test()

    # 运行连接测试
    test_connection()

    print("\n" + "=" * 50)
    print("测试完成")
    print("=" * 50)
    print("\n建议：")
    print("- 如果ping失败：检查网络和机器狗是否开机")
    print("- 如果ping成功但连接失败：检查是否配置数据上报")
    print("- 参考 '运动主机通讯接口.txt' 第4节配置数据上报")