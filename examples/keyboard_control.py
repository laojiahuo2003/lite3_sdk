"""Lite3机器人键盘控制示例（跨平台版本）

改进版：虚拟摇杆模式
- WASD + QR 控制移动（按住移动，松手自动停止，平滑加减速）
- 箭头键控制原地模式姿态
- Windows: 使用 GetAsyncKeyState 实时检测按键状态
- Linux/Mac: 使用时间戳超时方案
"""
import time
import sys
import threading
import platform
from lite3_sdk import Lite3Client
from lite3_sdk.models import RobotBasicState, RobotGaitState, RobotPolicyState


# =============================================================================
# 平台相关的键盘输入
# =============================================================================

if platform.system() == 'Windows':
    import msvcrt

    def getch():
        """Windows平台：获取单个字符输入"""
        if msvcrt.kbhit():
            ch = msvcrt.getch()
            # Python 3 中 msvcrt.getch() 返回 bytes，必须用 bytes 比较
            if ch == b'\xe0':  # Windows特殊键前缀（箭头键/F键）
                ch2 = msvcrt.getch()
                if ch2 == b'H':
                    return 'ARROW_A'  # 上
                elif ch2 == b'P':
                    return 'ARROW_B'  # 下
                elif ch2 == b'K':
                    return 'ARROW_D'  # 左
                elif ch2 == b'M':
                    return 'ARROW_C'  # 右
                return ch2
            if ch == b'\x1b':  # ESC
                return '\x1b'
            try:
                return ch.decode('utf-8')
            except:
                return ch
        return None
else:
    import tty
    import termios

    def getch():
        """Linux/Mac平台：获取单个字符输入（不等待回车）"""
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(sys.stdin.fileno())
            ch = sys.stdin.read(1)
            if ch == '\x1b':  # ESC序列开始
                ch2 = sys.stdin.read(1)
                ch3 = sys.stdin.read(1)
                if ch2 == '[':
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


# =============================================================================
# KeyboardController
# =============================================================================

class KeyboardController:
    """键盘控制器（虚拟摇杆模式）"""

    # ---- 移动控制键位（WASD + QE，FPS 游戏标准布局） ----
    KEY_FORWARD = 'w'       # W — 前进
    KEY_BACKWARD = 's'      # S — 后退
    KEY_TURN_LEFT = 'a'     # A — 左转
    KEY_TURN_RIGHT = 'd'    # D — 右转
    KEY_STRAFE_LEFT = 'q'   # Q — 左平移
    KEY_STRAFE_RIGHT = 'e'  # E — 右平移

    MOVEMENT_KEYS = ['w', 's', 'a', 'd', 'q', 'e']

    # ---- 参数 ----
    AXIS_MAX = 32767
    SMOOTH_RISE = 0.30      # 加速平滑因子（越大越快，0~1，每 tick 插值比例）
    SMOOTH_FALL = 0.20      # 减速平滑因子（稍慢一点，避免急停）
    MAX_SPEED = 20000        # "摇杆推到底"对应的轴指令值
    AXIS_RATE = 50.0         # 轴指令发送频率 (Hz)

    # 死区（协议 1.2.3.2 节）
    DEADZONE_PITCH = 6553
    DEADZONE_ROLL = 12553
    DEADZONE_YAW = 9553

    # 原地模式步长
    POSTURE_STEP = 5000

    def __init__(self, host: str = "192.168.2.1", port: int = 43893):
        self.client = Lite3Client(host=host, port=port)
        self.running = False

        # ---- 平滑移动控制（浮点内部值，发送时转 int） ----
        self._smooth_pitch = 0.0
        self._smooth_roll = 0.0
        self._smooth_yaw = 0.0

        # ---- 原地模式姿态步进值 ----
        self._posture_pitch = 0
        self._posture_roll = 0
        self._posture_yaw = 0
        self._posture_height = 0

        # ---- 按键状态追踪（Linux/Mac 时间戳方案用） ----
        self._key_timestamps: dict[str, float] = {}
        self._KEY_HOLD_TIMEOUT = 0.15  # 150ms 无重复按键则视为松键

        # ---- 平台相关的按键状态检测 ----
        self._init_key_detection()

        # ---- 轴指令发送线程 ----
        self._axis_thread: threading.Thread | None = None
        self._axis_running = False

    # =========================================================================
    # 平台相关：按键状态检测
    # =========================================================================

    def _init_key_detection(self):
        """初始化平台相关的按键状态检测。"""
        if platform.system() == 'Windows':
            import ctypes
            self._GetAsyncKeyState = ctypes.windll.user32.GetAsyncKeyState
            # 虚拟键码映射
            self._VK_MAP = {
                'w': 0x57, 's': 0x53, 'a': 0x41, 'd': 0x44,
                'q': 0x51, 'e': 0x45,
            }

    def _is_key_held(self, key_char: str) -> bool:
        """检测移动键是否正在被按住。

        Windows: 使用 GetAsyncKeyState（实时，零延迟）。
        Linux/Mac: 使用时间戳超时（~150ms 松键延迟）。
        """
        if platform.system() == 'Windows':
            vk = self._VK_MAP.get(key_char)
            if vk is not None:
                return (self._GetAsyncKeyState(vk) & 0x8000) != 0
            return False
        else:
            last = self._key_timestamps.get(key_char, 0)
            return (time.time() - last) < self._KEY_HOLD_TIMEOUT

    def _mark_key_pressed(self, key_char: str):
        """记录按键时间戳（Linux/Mac 松键检测用）。"""
        self._key_timestamps[key_char] = time.time()

    # =========================================================================
    # 连接管理
    # =========================================================================

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
        time.sleep(1)
        return True

    def disconnect(self):
        """断开连接"""
        self.running = False
        self._stop_axis_thread()
        self.client.disconnect()
        print("\n✅ 已断开连接")

    # =========================================================================
    # 轴指令线程（核心改进）
    # =========================================================================

    def _start_axis_thread(self):
        """启动轴指令发送线程"""
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

    def _compute_movement_targets(self):
        """根据当前按住的键计算目标轴指令值。

        Returns:
            (target_pitch, target_roll, target_yaw) — 每个轴的目标值
        """
        tp = 0.0
        tr = 0.0
        ty = 0.0

        # W/S — 前进/后退
        if self._is_key_held('w'):
            tp += self.MAX_SPEED
        if self._is_key_held('s'):
            tp -= self.MAX_SPEED

        # A/D — 左转/右转
        if self._is_key_held('a'):
            ty -= self.MAX_SPEED
        if self._is_key_held('d'):
            ty += self.MAX_SPEED

        # Q/E — 左平移/右平移
        if self._is_key_held('q'):
            tr -= self.MAX_SPEED
        if self._is_key_held('e'):
            tr += self.MAX_SPEED

        return tp, tr, ty

    def _axis_loop(self):
        """轴指令发送循环（50Hz）。

        核心逻辑：
        1. 检测 WASD/QR 哪些键被按住 → 计算目标值
        2. 平滑插值当前值 → 目标值（模拟摇杆物理行程）
        3. 发送轴指令
        4. 当所有键松开时，目标值=0，自动回中停止
        """
        while self._axis_running:
            # 1. 根据按键状态计算目标值
            target_pitch, target_roll, target_yaw = self._compute_movement_targets()

            # 2. 平滑插值（加速用 SMOOTH_RISE，减速用 SMOOTH_FALL）
            #    检查每个轴是加速还是减速，使用不同的平滑因子
            for attr, target, smooth_rise, smooth_fall in [
                ('_smooth_pitch', target_pitch, self.SMOOTH_RISE, self.SMOOTH_FALL),
                ('_smooth_roll', target_roll, self.SMOOTH_RISE, self.SMOOTH_FALL),
                ('_smooth_yaw', target_yaw, self.SMOOTH_RISE, self.SMOOTH_FALL),
            ]:
                current = getattr(self, attr)
                # |target| >= |current| 时用 rise，否则用 fall
                f = smooth_rise if abs(target) >= abs(current) else smooth_fall
                setattr(self, attr, current + (target - current) * f)

            # 3. 合并平滑值 + 原地模式姿态步进值
            pitch = int(self._smooth_pitch) + self._posture_pitch
            roll = int(self._smooth_roll) + self._posture_roll
            yaw = int(self._smooth_yaw) + self._posture_yaw
            height = self._posture_height

            # 4. 限幅后发送
            pitch = max(-self.AXIS_MAX, min(self.AXIS_MAX, pitch))
            roll = max(-self.AXIS_MAX, min(self.AXIS_MAX, roll))
            yaw = max(-self.AXIS_MAX, min(self.AXIS_MAX, yaw))

            self.client.set_pitch(pitch)
            self.client.set_roll(roll)
            self.client.set_yaw(yaw)
            self.client.set_height(height)

            time.sleep(1.0 / self.AXIS_RATE)

    # =========================================================================
    # 状态显示与菜单
    # =========================================================================

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

    def _show_movement_state(self):
        """显示当前移动轴值（调试用）"""
        pitch = int(self._smooth_pitch) + self._posture_pitch
        roll = int(self._smooth_roll) + self._posture_roll
        yaw = int(self._smooth_yaw) + self._posture_yaw
        print(f"轴值: pitch={pitch:+6d}  roll={roll:+6d}  yaw={yaw:+6d}  height={self._posture_height:+6d}")

    def print_menu(self):
        """打印控制菜单"""
        print("\n" + "=" * 60)
        print("Lite3 机器人键盘控制 — 虚拟摇杆模式")
        print(f"平台: {platform.system()}")
        print("=" * 60)

        print("\n【移动控制 — 按住移动，松手自动停止】")
        print("  W / S    前进 / 后退")
        print("  A / D    左转 / 右转")
        print("  Q / E    左平移 / 右平移")
        print("  支持组合键（如 W+D = 前进+右转）")
        print("  v        显示当前轴值")

        print("\n【原地模式 — 姿态调整（箭头键，步进式）】")
        print("  ↑ / ↓    调整俯仰角")
        print("  ← / →    调整横滚角")
        print("  h        重置所有轴指令/姿态")

        print("\n【模式切换】")
        print("  1        原地模式")
        print("  2        移动模式（配合 WASD 使用）")
        print("  3        手动模式")
        print("  4        自主模式")

        print("\n【AI模式】")
        print("  a        进入AI模式")
        print("  x        退出AI模式")

        print("\n【步态切换】")
        print("  u        低速步态")
        print("  i        中速步态")
        print("  o        高速步态")
        print("  l        切换匍匐步态")

        print("\n【基本控制】")
        print("  空格键   起立/趴下切换")
        print("  r        软急停")
        print("  z        回零")
        print("  Tab      显示当前状态")
        print("  ESC      退出程序")

        print("\n【动作指令】")
        print("  t        扭身体    f    翻身")
        print("  p        太空步    b    后空翻")
        print("  g        打招呼    j    向前跳")
        print("  y        扭身跳    c    停止动作")
        print("=" * 60)

    # =========================================================================
    # 按键处理
    # =========================================================================

    def handle_key(self, key):
        """处理按键输入"""
        if key is None:
            return True

        # ---- 移动控制（WASD + QE） ----
        if key in self.MOVEMENT_KEYS:
            self._mark_key_pressed(key)
            return True

        # ---- 轴值显示 ----
        if key == 'v':
            self._show_movement_state()
            return True

        # ---- 基本控制 ----
        if key == ' ':
            print("\n>>> 起立/趴下切换")
            self.client.stand_toggle()

        elif key == 'r':
            print("\n>>> 软急停")
            self.client.soft_estop()

        elif key == 'z':
            print("\n>>> 回零")
            self.client.zeroing()

        elif key == '\t':  # Tab
            self.show_status()

        elif key == '\x1b':
            print("\n>>> 退出程序")
            self.running = False
            return False

        # ---- 模式切换 ----
        elif key == '1':
            print("\n>>> 切换到原地模式（箭头键调整姿态）")
            self._reset_all_axis()
            self.client.set_in_place_mode()

        elif key == '2':
            print("\n>>> 切换到移动模式（WASD 控制移动）")
            self._reset_all_axis()
            self.client.set_moving_mode()

        elif key == '3':
            print("\n>>> 切换到手动模式")
            self.client.set_manual_mode()

        elif key == '4':
            print("\n>>> 切换到自主模式")
            self.client.set_autonomous_mode()

        # ---- AI模式 ----
        elif key == 'a':
            print("\n>>> 进入AI模式")
            self.client.enter_ai()

        elif key == 'x':
            print("\n>>> 退出AI模式")
            self.client.exit_ai()

        # ---- 步态切换 ----
        elif key == 'u':
            print("\n>>> 切换到低速步态")
            self.client.set_low_speed_gait()

        elif key == 'i':
            print("\n>>> 切换到中速步态")
            self.client.set_medium_speed_gait()

        elif key == 'o':
            print("\n>>> 切换到高速步态")
            self.client.set_high_speed_gait()

        elif key == 'l':
            print("\n>>> 切换匍匐步态")
            self.client.toggle_crawl_gait()

        # ---- 动作指令 ----
        elif key == 't':
            print("\n>>> 扭身体")
            self.client.twist_body()

        elif key == 'f':
            print("\n>>> 翻身")
            self.client.roll_over()

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

        elif key == 'p':
            print("\n>>> 太空步")
            self.client.space_walk()

        # ---- 原地模式姿态调整（箭头键，步进式） ----
        elif key == 'ARROW_A':  # 上箭头
            self._posture_pitch = min(self.AXIS_MAX, self._posture_pitch + self.POSTURE_STEP)
            print(f"\n>>> 俯仰角: {self._posture_pitch:+d}")

        elif key == 'ARROW_B':  # 下箭头
            self._posture_pitch = max(-self.AXIS_MAX, self._posture_pitch - self.POSTURE_STEP)
            print(f"\n>>> 俯仰角: {self._posture_pitch:+d}")

        elif key == 'ARROW_D':  # 左箭头
            self._posture_roll = max(-self.AXIS_MAX, self._posture_roll - self.POSTURE_STEP)
            print(f"\n>>> 横滚角: {self._posture_roll:+d}")

        elif key == 'ARROW_C':  # 右箭头
            self._posture_roll = min(self.AXIS_MAX, self._posture_roll + self.POSTURE_STEP)
            print(f"\n>>> 横滚角: {self._posture_roll:+d}")

        # ---- 重置 ----
        elif key == 'h':
            print("\n>>> 重置所有轴指令（停止移动 + 姿态归零）")
            self._reset_all_axis()

        return True

    def _reset_all_axis(self):
        """重置所有轴指令值"""
        self._smooth_pitch = 0.0
        self._smooth_roll = 0.0
        self._smooth_yaw = 0.0
        self._posture_pitch = 0
        self._posture_roll = 0
        self._posture_yaw = 0
        self._posture_height = 0
        self.client.stop_movement()

    # =========================================================================
    # 主循环
    # =========================================================================

    def run(self):
        """运行键盘控制"""
        if not self.connect():
            return

        self.print_menu()
        print("\n💡 提示:")
        print("   - 切换到移动模式（按2），然后用 WASD 控制移动")
        print("   - 按住移动，松手自动停止（虚拟摇杆）")
        print("   - 支持同时按住多个键（如 W+D 前进+右转）")
        print("   - 按 v 查看当前轴值")

        if platform.system() == 'Windows':
            print("   - Windows: GetAsyncKeyState 实时检测按键（零延迟）")
            print("开始监听键盘输入...\n")
        else:
            print("   - Linux/Mac: 时间戳超时检测（~150ms 松键延迟）")
            print("开始监听键盘输入...\n")

        self.running = True
        self._start_axis_thread()

        try:
            while self.running:
                if platform.system() == 'Windows':
                    key = getch()
                    if key:
                        if not self.handle_key(key):
                            break
                    time.sleep(0.01)  # 10ms 轮询间隔
                else:
                    key = getch()
                    if not self.handle_key(key):
                        break

        except KeyboardInterrupt:
            print("\n\n用户中断操作")
        finally:
            self.disconnect()


# =============================================================================
# 入口
# =============================================================================

def main():
    """主函数"""
    print("\n使用说明:")
    print("1. 确保机器人已开机并连接到网络")
    print("2. 修改 host 参数为你的机器人IP地址")
    print("3. 运行此脚本: python keyboard_control.py")
    print("4. 切换到移动模式（按2），然后用 WASD 控制移动")
    print("\n平台支持:")
    print(f"- 当前平台: {platform.system()}")
    print("- Windows: 使用 msvcrt + GetAsyncKeyState（无需额外依赖）")
    print("- Linux/Mac: 使用 tty/termios（无需额外依赖）")
    print("\n改进要点:")
    print("- ✅ 虚拟摇杆模式：按住移动，松手自动停止")
    print("- ✅ 平滑加减速（模拟摇杆物理行程）")
    print("- ✅ 支持组合键（W+D 前进+右转）")
    print("- ✅ WASD + QR 布局（FPS 游戏标准，直觉化）")
    print("- ✅ Windows 实时按键检测（零延迟）")
    print("\n")

    controller = KeyboardController(host="192.168.2.1", port=43893)
    controller.run()


if __name__ == "__main__":
    main()
