"""Lite3 机器人状态实时监控

跨平台终端 UI（Windows / Linux），实时显示机器人全部状态字段。
零额外依赖，仅使用 ANSI 转义序列清屏刷新。

用法:
    python status_monitor.py [--host IP] [--port PORT] [--local-port PORT] [--rate HZ]

按键:
    q / ESC — 退出
"""

import argparse
import os
import signal
import sys
import time
from lite3_sdk import Lite3Client


# =============================================================================
# 终端控制（跨平台 ANSI）
# =============================================================================

class Terminal:
    """跨平台终端控制"""

    @staticmethod
    def setup():
        """启用 ANSI 支持（Windows 需要）"""
        if os.name == 'nt':
            import ctypes
            kernel32 = ctypes.windll.kernel32
            kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)

    @staticmethod
    def clear():
        """清屏并将光标置于左上角"""
        sys.stdout.write('\033[H\033[J')

    @staticmethod
    def cursor_hide():
        sys.stdout.write('\033[?25l')

    @staticmethod
    def cursor_show():
        sys.stdout.write('\033[?25h')

    @staticmethod
    def flush():
        sys.stdout.flush()


# =============================================================================
# 格式化
# =============================================================================

def fmt_ok(val) -> str:
    return f'\033[92m{val}\033[0m'  # 绿色


def fmt_warn(val) -> str:
    return f'\033[93m{val}\033[0m'  # 黄色


def fmt_dim(val) -> str:
    return f'\033[90m{val}\033[0m'  # 灰色


def bar(val, width=20, max_val=100):
    """绘制进度条"""
    pct = min(max(val / max_val, 0), 1)
    filled = int(pct * width)
    bar_str = '█' * filled + '░' * (width - filled)
    if pct > 0.5:
        color = '\033[92m'  # 绿
    elif pct > 0.2:
        color = '\033[93m'  # 黄
    else:
        color = '\033[91m'  # 红
    return f'{color}{bar_str}\033[0m'


# =============================================================================
# 渲染
# =============================================================================

def render(state, count: int, elapsed: float, rate: float) -> str:
    """渲染完整状态界面"""
    lines = []

    # 标题栏
    batt_pct = state.battery_percentage
    batt_bar = bar(batt_pct, 20, 100)
    title = (f" Lite3 状态监控 "
             f"│ 收包: {count:6d}  "
             f"│ 频率: {rate:5.1f} Hz  "
             f"│ 运行: {int(elapsed)//60:02d}:{int(elapsed)%60:02d}")
    lines.append('=' * 70)
    lines.append(title)
    lines.append('=' * 70)

    # --- 状态行 ---
    state_color = '\033[92m' if state.is_standing else '\033[93m'
    lines.append(f"  状态: {state_color}{state.basic_state_name:<20s}\033[0m  "
                 f"步态: {state.gait_state_name:<20s}  "
                 f"AI:   {state.policy_state_name:<20s}")
    lines.append(f"  动作: {state.motion_state_name:<20s}  "
                 f"电池: {batt_pct:5.1f}% {batt_bar}")

    # --- IMU ---
    lines.append('')
    lines.append('  ── IMU 姿态角 (°) ─────────────────────────────────────')
    lines.append(f'    Roll {state.roll:+10.3f}°    Pitch {state.pitch:+10.3f}°    Yaw {state.yaw:+10.3f}°')

    lines.append('')
    lines.append('  ── IMU 角速度 (rad/s) ──────────────────────────────────')
    lines.append(f'    Roll {state.roll_vel:+10.4f}     Pitch {state.pitch_vel:+10.4f}     Yaw {state.yaw_vel:+10.4f}')

    lines.append('')
    lines.append('  ── IMU 加速度 (m/s²) ──────────────────────────────────')
    g_ok = abs(state.z_acc - 9.8) < 1.5
    z_str = f'{state.z_acc:+10.4f}' + (' ≈g' if g_ok else '')
    lines.append(f'    X  {state.x_acc:+10.4f}     Y  {state.y_acc:+10.4f}     Z  {z_str}')

    # --- 位姿 & 速度 ---
    lines.append('')
    lines.append('  ── 世界坐标系 ─────────────────────────────────────────')
    lines.append(f'    位置  x={state.pos_x:+8.3f}m   y={state.pos_y:+8.3f}m   yaw={state.pos_yaw:+8.4f}rad')
    lines.append(f'    速度  x={state.vel_x_world:+8.4f}   y={state.vel_y_world:+8.4f}   yaw={state.vel_yaw_world:+8.4f}')

    lines.append('')
    lines.append('  ── 身体坐标系速度 ─────────────────────────────────────')
    lines.append(f'    x={state.vel_x_body:+8.4f}   y={state.vel_y_body:+8.4f}   yaw={state.vel_yaw_body:+8.4f}')

    # --- 超声波 ---
    lines.append('')
    us_fwd = state.ultrasound_forward
    us_bwd = state.ultrasound_backward
    us_fwd_s = fmt_warn(f'{us_fwd:.3f}m') if us_fwd < 0.5 else f'{us_fwd:.3f}m'
    us_bwd_s = fmt_warn(f'{us_bwd:.3f}m') if us_bwd < 0.5 else f'{us_bwd:.3f}m'
    lines.append(f'  ── 超声波 ─────────────────────────────────────────────')
    lines.append(f'    前方: {us_fwd_s}     后方: {us_bwd_s}')

    # --- 标志位 ---
    lines.append('')
    lines.append('  ── 标志位 ─────────────────────────────────────────────')
    flags = []
    flags.append(('平衡', state.is_robot_need_move, True))  # True=正常(可保持平衡)
    flags.append(('回零', state.zero_position_flag, True))
    flags.append(('首次启动', state.is_after_first_start, False))
    flags.append(('语音控制', state.is_voice_ctrl_enable, False))
    flags.append(('充电', state.is_charging, False))

    flag_strs = []
    for name, val, good_when_true in flags:
        if val:
            s = fmt_ok(name) if good_when_true else fmt_warn(name)
        else:
            s = fmt_warn(name) if good_when_true else fmt_dim(name)
        flag_strs.append(f'{s}={val}')
    lines.append('    ' + '  '.join(flag_strs))

    # --- 底部 ---
    lines.append('')
    lines.append('=' * 70)
    lines.append(f'  q/ESC 退出  │  固件版本: {state.version}  │  错误码: {state.error_state}')
    lines.append('=' * 70)

    return '\n'.join(lines)


# =============================================================================
# 键盘输入（跨平台非阻塞）
# =============================================================================

def get_key_nonblock():
    """非阻塞获取按键（跨平台）"""
    if os.name == 'nt':
        import msvcrt
        if msvcrt.kbhit():
            ch = msvcrt.getch()
            if ch == b'\xe0':
                msvcrt.getch()  # 丢弃特殊键第二部分
                return None
            if ch == b'\x1b':
                return '\x1b'
            try:
                return ch.decode('utf-8').lower()
            except:
                return None
        return None
    else:
        import termios
        fd = sys.stdin.fileno()
        old = termios.tcgetattr(fd)
        new = termios.tcgetattr(fd)
        new[3] = new[3] & ~termios.ICANON & ~termios.ECHO
        new[6][termios.VMIN] = 0
        new[6][termios.VTIME] = 0
        termios.tcsetattr(fd, termios.TCSANOW, new)
        ch = sys.stdin.read(1)
        termios.tcsetattr(fd, termios.TCSAFLUSH, old)
        if ch == '\x1b':
            return '\x1b'
        return ch.lower() if ch else None


# =============================================================================
# 主循环
# =============================================================================

def run_monitor(host: str, port: int, local_port: int, rate: float = 10.0):
    """运行状态监控"""
    Terminal.setup()
    Terminal.cursor_hide()

    client = Lite3Client(host=host, port=port, local_port=local_port)

    print(f"正在连接 {host}:{port} (本机端口={local_port})...")
    if not client.connect(verify=True):
        print("连接失败！")
        Terminal.cursor_show()
        return

    client.start_heartbeat(rate=5.0)
    print("已连接，等待状态数据...")
    time.sleep(2)  # 等首条状态到达

    count = 0
    last_count = 0
    last_time = time.time()
    start_time = time.time()
    display_rate = 0.0

    def on_state(s):
        nonlocal count
        count += 1
    client.set_robot_state_callback(on_state)

    interval = 1.0 / rate

    try:
        while True:
            frame_start = time.time()

            # 检查按键
            key = get_key_nonblock()
            if key in ('q', '\x1b'):
                break

            # 计算显示频率
            now = time.time()
            if now - last_time >= 1.0:
                display_rate = (count - last_count) / (now - last_time)
                last_count = count
                last_time = now

            # 渲染
            state = client.robot_state
            if state is not None:
                elapsed = now - start_time
                output = render(state, count, elapsed, display_rate)
                Terminal.clear()
                sys.stdout.write(output)
            else:
                Terminal.clear()
                sys.stdout.write('\n\n')
                sys.stdout.write('  ⏳ 等待状态数据...\n')
                sys.stdout.write(f'  已收包: {count}\n')
                if count == 0:
                    sys.stdout.write('\n  请确认机器人数据上报目标地址包含本机\n')

            Terminal.flush()

            # 帧率控制
            elapsed_frame = time.time() - frame_start
            sleep_time = interval - elapsed_frame
            if sleep_time > 0:
                time.sleep(sleep_time)

    except KeyboardInterrupt:
        pass
    finally:
        Terminal.clear()
        Terminal.cursor_show()
        print("正在断开...")
        client.stop_heartbeat()
        client.disconnect()
        print("已退出。")


# =============================================================================
# 入口
# =============================================================================

def main():
    parser = argparse.ArgumentParser(description='Lite3 机器人状态实时监控')
    parser.add_argument('--host', default='192.168.0.37', help='运动主机 IP')
    parser.add_argument('--port', type=int, default=43893, help='运动主机端口')
    parser.add_argument('--local-port', type=int, default=43897, help='本机绑定端口')
    parser.add_argument('--rate', type=float, default=10.0, help='刷新频率 (Hz)')
    args = parser.parse_args()

    run_monitor(args.host, args.port, args.local_port, args.rate)


if __name__ == '__main__':
    main()
