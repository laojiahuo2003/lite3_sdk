"""Lite3机器人键盘控制示例"""
import time
import sys
import threading
import tty
import termios
from lite3_sdk import Lite3Client
from lite3_sdk.models import RobotBasicState, RobotGaitState, RobotPolicyState


def getch():
    """获取单个字符输入（不等待回车）"""
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(sys.stdin.fileno())
        ch = sys.stdin.read(1)
        # 处理特殊键（箭头键等）
        if ch == '\x1b':  # ESC序列开始
            ch2 = sys.stdin.read(1)
            ch3 = sys.stdin.read(1)
            if ch2 == '[':
                # 箭头键: ESC[A (上), ESC[B (下), ESC[C (右), ESC[D (左)
                # F1-F4: ESC[11~ 到 ESC[14~
                if ch3 in 'ABCD':
                    return f'ARROW_{ch3}'
                elif ch3 == '1':
                    ch4 = sys.stdin.read(1)
                    if ch4 == '~':
                        return 'F1'
                elif ch3 == '2':
                    ch4 = sys.stdin.read(1)
                    if ch4 == '~':
                        return 'F2'
                elif ch3 == '3':
                    ch4 = sys.stdin.read(1)
                    if ch4 == '~':
                        return 'F3'
                elif ch3 == '4':
                    ch4 = sys.stdin.read(1)
                    if ch4 == '~':
                        return 'F4'
        return ch
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)


class KeyboardController:
    """键盘控制器"""

    def __init__(self, host: str = "192.168.2.1", port: int = 43893):
        """
        初始化键盘控制器

        Args:
            host: 机器人IP地址
            port: 机器人端口
        """
        self.client = Lite3Client(host=host, port=port)
        self.running = False

        # 轴指令值（用于原地模式调整姿态 + 移动模式控制速度）
        self.roll_value = 0      # 原地模式:横滚角 / 移动模式:左右平移速度
        self.pitch_value = 0     # 原地模式:俯仰角 / 移动模式:前后平移速度
        self.yaw_value = 0       # 原地模式:偏航角 / 移动模式:左右转弯速度
        self.height_value = 0    # 身体高度

        # 轴指令死区（协议1.2.3.2节）
        self.DEADZONE_PITCH = 6553    # 前后平移死区
        self.DEADZONE_ROLL = 12553    # 左右平移死区
        self.DEADZONE_YAW = 9553      # 转弯死区

        # 轴指令步长
        self.AXIS_STEP_PITCH = 5000
        self.AXIS_STEP_ROLL = 5000
        self.AXIS_STEP_YAW = 5000

        # 持续发送轴指令的线程（移动模式下需 ≥20Hz 频率发送）
        self._axis_thread: threading.Thread | None = None
        self._axis_running = False
        self._axis_rate = 50.0  # 50Hz 发送频率

    def connect(self) -> bool:
        """连接机器人"""
        print("正在连接机器人...")
        if not self.client.connect(verify=True):
            print("❌ 连接失败！")
            print("   请检查：")
            print("   1. 机器狗是否已开机")
            print("   2. 网络连接是否正常")
            print("   3. IP地址是否正确")
            return False

        print("✅ 连接成功")
        self.client.start_heartbeat(rate=5.0)
        print("✅ 心跳已启动")

        # 等待接收状态
        time.sleep(1)
        return True

    def disconnect(self):
        """断开连接"""
        self.running = False
        self._stop_axis_thread()
        self.client.disconnect()
        print("\n✅ 已断开连接")

    def _start_axis_thread(self):
        """启动持续发送轴指令的线程（移动模式下需要 ≥20Hz）"""
        if self._axis_running:
            return
        self._axis_running = True
        self._axis_thread = threading.Thread(target=self._axis_loop, daemon=True)
        self._axis_thread.start()

    def _stop_axis_thread(self):
        """停止轴指令发送线程"""
        self._axis_running = False
        if self._axis_thread:
            self._axis_thread.join(timeout=2.0)
            self._axis_thread = None

    def _axis_loop(self):
        """持续发送轴指令（50Hz），确保不超过250ms超时"""
        while self._axis_running:
            # 发送所有轴指令（在移动模式下这些控制速度）
            self.client.set_pitch(self.pitch_value)
            self.client.set_roll(self.roll_value)
            self.client.set_yaw(self.yaw_value)
            self.client.set_height(self.height_value)
            time.sleep(1.0 / self._axis_rate)

    def _apply_axis_deadzone(self, value: int, deadzone: int) -> int:
        """应用死区：死区范围内的值视为0"""
        if abs(value) < deadzone:
            return 0
        return value

    def show_status(self):
        """显示当前状态"""
        if self.client.robot_state:
            state = self.client.robot_state
            print(f"\n当前状态: {state.basic_state_name}")
            print(f"步态: {state.gait_state_name}")
            print(f"AI步态: {state.policy_state_name}")
            print(f"电池: {state.battery_percentage:.1f}%")
            print(f"姿态: roll={state.roll:.1f}° pitch={state.pitch:.1f}° yaw={state.yaw:.1f}°")
        else:
            print("\n⚠️  未接收到状态数据")

    def print_menu(self):
        """打印控制菜单"""
        print("\n" + "=" * 60)
        print("Lite3机器人键盘控制")
        print("=" * 60)
        print("\n【基本控制】")
        print("  空格键  - 起立/趴下切换")
        print("  e       - 软急停")
        print("  z       - 回零")
        print("  s       - 显示当前状态")
        print("  q/ESC   - 退出程序")
        print("\n【模式切换】")
        print("  1       - 原地模式")
        print("  2       - 移动模式")
        print("  3       - 手动模式")
        print("  4       - 自主模式")
        print("\n【AI模式】")
        print("  a       - 进入AI模式")
        print("  x       - 退出AI模式")
        print("\n【步态切换】")
        print("  F1      - 低速步态")
        print("  F2      - 中速步态")
        print("  F3      - 高速步态")
        print("  F4      - 切换匍匐步态")
        print("\n【动作指令】")
        print("  t       - 扭身体")
        print("  r       - 翻身")
        print("  w       - 太空步")
        print("  b       - 后空翻")
        print("  g       - 打招呼")
        print("  j       - 向前跳")
        print("  y       - 扭身跳")
        print("  c       - 停止动作")
        print("\n【轴指令（原地模式）】")
        print("  ↑/↓     - 调整俯仰角/前后平移")
        print("  ←/→     - 调整横滚角/左右平移")
        print("  h       - 重置所有轴指令")
        print("\n【速度指令（移动模式 mode=2）】")
        print("  i/k     - 前进/后退")
        print("  l/m     - 右移/左移")
        print("  u/o     - 左转/右转")
        print("  ⚠️  需要先切换到移动模式（按2），轴指令会持续发送(50Hz)")
        print("=" * 60)

    def handle_key(self, key):
        """处理按键输入"""
        # 基本控制
        if key == ' ':  # 空格键
            print("\n>>> 起立/趴下切换")
            self.client.stand_toggle()

        elif key == 'e':
            print("\n>>> 软急停")
            self.client.soft_estop()

        elif key == 'z':
            print("\n>>> 回零")
            self.client.zeroing()

        elif key == 's':
            self.show_status()

        elif key == 'q' or key == '\x1b':  # q 或 ESC
            print("\n>>> 退出程序")
            self.running = False
            return False

        # 模式切换
        elif key == '1':
            print("\n>>> 切换到原地模式")
            self.client.set_in_place_mode()

        elif key == '2':
            print("\n>>> 切换到移动模式")
            self.client.set_moving_mode()

        elif key == '3':
            print("\n>>> 切换到手动模式")
            self.client.set_manual_mode()

        elif key == '4':
            print("\n>>> 切换到自主模式（速度指令由感知主机下发）")
            self.client.set_autonomous_mode()

        # AI模式
        elif key == 'a':
            print("\n>>> 进入AI模式")
            self.client.enter_ai()

        elif key == 'x':
            print("\n>>> 退出AI模式")
            self.client.exit_ai()

        # 步态切换
        elif key == 'F1':
            print("\n>>> 切换到低速步态")
            self.client.set_low_speed_gait()

        elif key == 'F2':
            print("\n>>> 切换到中速步态")
            self.client.set_medium_speed_gait()

        elif key == 'F3':
            print("\n>>> 切换到高速步态")
            self.client.set_high_speed_gait()

        elif key == 'F4':
            print("\n>>> 切换匍匐步态")
            self.client.toggle_crawl_gait()

        # 动作指令
        elif key == 't':
            print("\n>>> 扭身体")
            self.client.twist_body()

        elif key == 'r':
            print("\n>>> 翻身")
            self.client.roll_over()

        elif key == 'w':
            print("\n>>> 太空步")
            self.client.space_walk()

        elif key == 'b':
            print("\n>>> 后空翻")
            self.client.backflip()

        elif key == 'g':
            print("\n>>> 打招呼")
            self.client.greeting()

        elif key == 'j':
            print("\n>>> 向前跳")
            self.client.jump_forward()

        elif key == 'y':
            print("\n>>> 扭身跳")
            self.client.twist_jump()

        elif key == 'c':
            print("\n>>> 停止动作")
            self.client.stop_action()

        # 轴指令（箭头键）
        elif key == 'ARROW_A':  # 上箭头
            self.pitch_value = min(32767, self.pitch_value + 5000)
            print(f"\n>>> 俯仰角/前移: {self.pitch_value}")
            self.client.set_pitch(self.pitch_value)

        elif key == 'ARROW_B':  # 下箭头
            self.pitch_value = max(-32767, self.pitch_value - 5000)
            print(f"\n>>> 俯仰角/后移: {self.pitch_value}")
            self.client.set_pitch(self.pitch_value)

        elif key == 'ARROW_D':  # 左箭头
            self.roll_value = max(-32767, self.roll_value - 5000)
            print(f"\n>>> 横滚角/左移: {self.roll_value}")
            self.client.set_roll(self.roll_value)

        elif key == 'ARROW_C':  # 右箭头
            self.roll_value = min(32767, self.roll_value + 5000)
            print(f"\n>>> 横滚角/右移: {self.roll_value}")
            self.client.set_roll(self.roll_value)

        elif key == 'h':
            print("\n>>> 重置所有轴指令")
            self.roll_value = 0
            self.pitch_value = 0
            self.yaw_value = 0
            self.height_value = 0
            self.client.set_roll(0)
            self.client.set_pitch(0)
            self.client.set_yaw(0)
            self.client.set_height(0)

        # 速度指令（移动模式下通过轴指令控制，轴线程持续发送）
        elif key == 'i':
            if self.pitch_value == 0:
                self.pitch_value = self.DEADZONE_PITCH + 1000  # 首次按下跳过死区
            else:
                self.pitch_value = min(32767, self.pitch_value + self.AXIS_STEP_PITCH)
            effective = self._apply_axis_deadzone(self.pitch_value, self.DEADZONE_PITCH)
            print(f"\n>>> 前进: raw={self.pitch_value}, effective={effective}")

        elif key == 'k':
            if self.pitch_value == 0:
                self.pitch_value = -(self.DEADZONE_PITCH + 1000)  # 首次按下跳过死区
            else:
                self.pitch_value = max(-32767, self.pitch_value - self.AXIS_STEP_PITCH)
            effective = self._apply_axis_deadzone(self.pitch_value, self.DEADZONE_PITCH)
            print(f"\n>>> 后退: raw={self.pitch_value}, effective={effective}")

        elif key == 'l':
            if self.roll_value == 0:
                self.roll_value = self.DEADZONE_ROLL + 1000  # 首次按下跳过死区
            else:
                self.roll_value = min(32767, self.roll_value + self.AXIS_STEP_ROLL)
            effective = self._apply_axis_deadzone(self.roll_value, self.DEADZONE_ROLL)
            print(f"\n>>> 右移: raw={self.roll_value}, effective={effective}")

        elif key == 'm':
            if self.roll_value == 0:
                self.roll_value = -(self.DEADZONE_ROLL + 1000)  # 首次按下跳过死区
            else:
                self.roll_value = max(-32767, self.roll_value - self.AXIS_STEP_ROLL)
            effective = self._apply_axis_deadzone(self.roll_value, self.DEADZONE_ROLL)
            print(f"\n>>> 左移: raw={self.roll_value}, effective={effective}")

        elif key == 'u':
            if self.yaw_value == 0:
                self.yaw_value = -(self.DEADZONE_YAW + 1000)  # 首次按下跳过死区
            else:
                self.yaw_value = max(-32767, self.yaw_value - self.AXIS_STEP_YAW)
            effective = self._apply_axis_deadzone(self.yaw_value, self.DEADZONE_YAW)
            print(f"\n>>> 左转: raw={self.yaw_value}, effective={effective}")

        elif key == 'o':
            if self.yaw_value == 0:
                self.yaw_value = self.DEADZONE_YAW + 1000  # 首次按下跳过死区
            else:
                self.yaw_value = min(32767, self.yaw_value + self.AXIS_STEP_YAW)
            effective = self._apply_axis_deadzone(self.yaw_value, self.DEADZONE_YAW)
            print(f"\n>>> 右转: raw={self.yaw_value}, effective={effective}")

        return True

    def run(self):
        """运行键盘控制"""
        if not self.connect():
            return

        self.print_menu()
        print("\n提示: 按键后动作会立即执行，按s查看当前状态")
        print("开始监听键盘输入...\n")

        self.running = True
        # 启动持续发送轴指令的线程（50Hz，避免250ms超时）
        self._start_axis_thread()

        try:
            while self.running:
                # 读取键盘输入
                key = getch()

                # 处理按键
                if not self.handle_key(key):
                    break

        except KeyboardInterrupt:
            print("\n\n用户中断操作")
        finally:
            self.disconnect()


def main():
    """主函数"""
    print("\n使用说明:")
    print("1. 确保机器人已开机并连接到网络")
    print("2. 修改 host 参数为你的机器人IP地址")
    print("3. 运行此脚本: python keyboard_control.py")
    print("4. 使用键盘控制机器人")
    print("\n注意:")
    print("- 使用标准终端输入，无需额外依赖库")
    print("- 按键后动作会立即执行")
    print("- 按s可以查看当前状态")
    print("- 按q或ESC退出程序")
    print("\n")

    # 创建控制器（修改为你的机器人IP）
    controller = KeyboardController(host="192.168.2.1", port=43893)
    controller.run()


if __name__ == "__main__":
    main()