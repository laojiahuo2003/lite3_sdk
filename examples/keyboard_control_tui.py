"""Lite3 机器人键盘控制 — TUI 版本

实时终端界面：面板化布局，机器人状态/轴指令/按键状态。
跨平台（Windows/Linux），零额外依赖，ANSI 转义序列。

用法:
    python keyboard_control_tui.py [--host IP] [--port PORT] [--local-port PORT]
"""

import argparse
import os
import re
import shutil
import sys
import time
import threading
import platform

from lite3_sdk import Lite3Client

# =============================================================================
# ANSI 终端控制
# =============================================================================

CSI = '\033['


def ansi(*codes):
    return CSI + ';'.join(str(c) for c in codes)


def setup_terminal():
    """启用 ANSI / 隐藏光标"""
    if os.name == 'nt':
        import ctypes
        kernel32 = ctypes.windll.kernel32
        kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
    sys.stdout.write(ansi('?25l'))  # 隐藏光标
    sys.stdout.flush()


def restore_terminal():
    sys.stdout.write(ansi('?25h'))  # 显示光标
    sys.stdout.write('\033[0m')     # 重置颜色
    sys.stdout.flush()


def term_size(default_w=80, default_h=24):
    """获取终端尺寸"""
    try:
        cs = shutil.get_terminal_size((default_w, default_h))
        return max(60, cs.columns), max(20, cs.lines)
    except Exception:
        return default_w, default_h


# =============================================================================
# 颜色快捷方式
# =============================================================================

def c(s, code=''):
    """包裹 ANSI 颜色"""
    if not code:
        return s
    return f'\033[{code}m{s}\033[0m'


GREEN = '92'; YELLOW = '93'; RED = '91'; CYAN = '96'; MAGENTA = '95'
DIM = '90'; BOLD = '1'; WHITE = '97'; BLUE = '94'


def _visible_len(s):
    """计算去掉 ANSI 转义码后的视觉长度"""
    return len(re.sub(r'\x1b\[[0-9;]*m', '', s))


def _vis_pad(s, width):
    """按视觉宽度左对齐填充"""
    pad = width - _visible_len(s)
    return s + ' ' * max(0, pad)


# =============================================================================
# 键盘输入
# =============================================================================

if platform.system() == 'Windows':
    import msvcrt
    import ctypes

    def _win_vk(key):
        return {'w': 0x57, 's': 0x53, 'a': 0x41, 'd': 0x44,
                'q': 0x51, 'e': 0x45}.get(key, 0)

    def is_key_held_win(key):
        vk = _win_vk(key)
        return vk and (ctypes.windll.user32.GetAsyncKeyState(vk) & 0x8000) != 0

    def getch():
        if msvcrt.kbhit():
            ch = msvcrt.getch()
            if ch == b'\xe0':
                ch2 = msvcrt.getch()
                return {'H': 'ARROW_A', 'P': 'ARROW_B',
                        'K': 'ARROW_D', 'M': 'ARROW_C'}.get(ch2, None)
            if ch == b'\x1b':
                return '\x1b'
            try:
                return ch.decode('utf-8')
            except Exception:
                return None
        return None
else:
    import termios

    def getch():
        fd = sys.stdin.fileno()
        old = termios.tcgetattr(fd)
        new = termios.tcgetattr(fd)
        new[3] = new[3] & ~termios.ICANON & ~termios.ECHO
        new[6][termios.VMIN] = 0
        new[6][termios.VTIME] = 0
        termios.tcsetattr(fd, termios.TCSANOW, new)
        ch = sys.stdin.read(1)
        if ch == '\x1b':
            c2 = sys.stdin.read(1)
            c3 = sys.stdin.read(1)
            termios.tcsetattr(fd, termios.TCSAFLUSH, old)
            if c2 == '[' and c3 in 'ABCD':
                return f'ARROW_{c3}'
            return '\x1b'
        termios.tcsetattr(fd, termios.TCSAFLUSH, old)
        return ch.lower() if ch else None

    def is_key_held_win(key):
        return False  # Linux 用时间戳方案


# =============================================================================
# UI 组件
# =============================================================================

def bar(value, width=16):
    """双向进度条：左侧负值(红)，右侧正值(绿)，0 在中间"""
    vmax = 32767
    half = width // 2
    pct = max(-1.0, min(1.0, value / vmax))
    if pct >= 0:
        n = int(pct * half)
        s = ' ' * half + '│' + c('█' * n, GREEN) + ' ' * (half - n)
    else:
        n = int(-pct * half)
        s = ' ' * (half - n) + c('█' * n, RED) + '│' + ' ' * half
    return s


def battery_bar(pct, width=10):
    """电池条 [██████    ] 带颜色"""
    if pct > 60:
        color = GREEN
    elif pct > 20:
        color = YELLOW
    else:
        color = RED
    filled = int(pct / 100.0 * width + 0.5)
    filled = max(0, min(width, filled))
    bar_s = '█' * filled + ' ' * (width - filled)
    return c(f'[{bar_s}]', color)


def key_indicator(letter, held):
    """单个按键指示灯"""
    if held:
        return c(f'[{letter}]', GREEN + ';' + BOLD)
    return c(f' {letter} ', DIM)


# =============================================================================
# 边框绘制
# =============================================================================

BORDER = {
    'tl': '┌', 'tr': '┐', 'bl': '└', 'br': '┘',
    'h': '─', 'v': '│',
    'lt': '├', 'rt': '┤', 'tt': '┬', 'bt': '┴',
}


def box_top(width, title=''):
    """┌── title ──...──┐"""
    if title:
        inner = f' {title} '
        w = width - 2
        left = (w - _visible_len(inner)) // 2
        right = w - _visible_len(inner) - left
        return BORDER['tl'] + BORDER['h'] * left + inner + BORDER['h'] * right + BORDER['tr']
    return BORDER['tl'] + BORDER['h'] * (width - 2) + BORDER['tr']


def box_bottom(width):
    """└──────────────┘"""
    return BORDER['bl'] + BORDER['h'] * (width - 2) + BORDER['br']


def box_sep(width, style='single'):
    """├──────────────┤ 分隔线"""
    if style == 'single':
        return BORDER['lt'] + BORDER['h'] * (width - 2) + BORDER['rt']
    return BORDER['h'] * width


def box_line(width, text, align='<'):
    """│ text              │"""
    txt = _vis_pad(text, width - 2) if align == '<' else text.rjust(width - 2)
    return BORDER['v'] + txt + BORDER['v']


# =============================================================================
# TuiController
# =============================================================================

class TuiController:
    """TUI 键盘控制器"""

    AXIS_MAX = 32767
    SMOOTH_RISE = 0.30
    SMOOTH_FALL = 0.20
    MAX_SPEED = 20000
    AXIS_RATE = 50.0
    POSTURE_STEP = 5000

    KEYS_MOVEMENT = ['w', 's', 'a', 'd', 'q', 'e']

    # ── 按键分发表 ──
    KEY_ACTIONS = {
        ' ':  ('stand_toggle',    '起立/趴下切换'),
        'r':  ('soft_estop',      '软急停'),
        'z':  ('zeroing',         '回零'),
        '1':  ('in_place_mode',   '原地模式'),
        '2':  ('moving_mode',     '移动模式'),
        '3':  ('manual_mode',     '手动模式'),
        '4':  ('autonomous_mode', '自主模式'),
        'u':  ('low_speed_gait',  '低速步态'),
        'i':  ('medium_speed_gait','中速步态'),
        'o':  ('high_speed_gait', '高速步态'),
        'l':  ('toggle_crawl',    '切换匍匐'),
        't':  ('twist_body',      '扭身体'),
        'f':  ('roll_over',       '翻身'),
        'b':  ('backflip',        '后空翻'),
        'g':  ('greeting',        '打招呼'),
        'j':  ('jump_forward',    '向前跳'),
        'y':  ('twist_jump',      '扭身跳'),
        'c':  ('stop_action',     '停止动作'),
        'p':  ('space_walk',      '太空步'),
        'h':  ('reset_axis',      '重置轴指令'),
        'a':  ('enter_ai',        '进入AI'),
        'x':  ('exit_ai',         '退出AI'),
    }

    def __init__(self, host, port, local_port):
        self.client = Lite3Client(host=host, port=port, local_port=local_port)

        # 轴值
        self._sp = 0.0  # smooth pitch
        self._sr = 0.0  # smooth roll
        self._sy = 0.0  # smooth yaw
        self._pp = 0    # posture pitch
        self._pr = 0    # posture roll
        self._py = 0    # posture yaw
        self._ph = 0    # posture height

        # 统计 (受锁保护)
        self._stats_lock = threading.Lock()
        self._pkt_count = 0
        self._last_pkt_time = 0.0
        self._start_time = 0.0
        self._last_key = ''
        self._last_msg = ''

        # 运行状态
        self.running = False
        self._axis_running = False
        self._axis_thread = None

        # Linux 按键时间戳
        self._key_ts = {}
        self._KEY_TIMEOUT = 0.15

    # ========== 连接 ==========

    def connect(self):
        if not self.client.connect(verify=True):
            return False
        self.client.start_heartbeat(rate=5.0)

        def on_state(s):
            with self._stats_lock:
                self._pkt_count += 1
                self._last_pkt_time = time.time()
        self.client.set_robot_state_callback(on_state)
        time.sleep(1)
        return True

    def disconnect(self):
        self.running = False
        self._stop_axis()
        self.client.disconnect()

    # ========== 轴指令线程 ==========

    def _start_axis(self):
        if self._axis_running:
            return
        self._axis_running = True
        self._axis_thread = threading.Thread(target=self._axis_loop, daemon=True)
        self._axis_thread.start()

    def _stop_axis(self):
        self._axis_running = False
        if self._axis_thread:
            self._axis_thread.join(timeout=2.0)

    def _is_movement_held(self, key):
        if platform.system() == 'Windows':
            return is_key_held_win(key)
        return (time.time() - self._key_ts.get(key, 0)) < self._KEY_TIMEOUT

    def _mark_key(self, key):
        self._key_ts[key] = time.time()

    def _axis_loop(self):
        while self._axis_running:
            tp = tr = ty = 0.0
            if self._is_movement_held('w'): tp += self.MAX_SPEED
            if self._is_movement_held('s'): tp -= self.MAX_SPEED
            if self._is_movement_held('a'): ty -= self.MAX_SPEED
            if self._is_movement_held('d'): ty += self.MAX_SPEED
            if self._is_movement_held('q'): tr -= self.MAX_SPEED
            if self._is_movement_held('e'): tr += self.MAX_SPEED

            for attr, target, rise, fall in [
                ('_sp', tp, self.SMOOTH_RISE, self.SMOOTH_FALL),
                ('_sr', tr, self.SMOOTH_RISE, self.SMOOTH_FALL),
                ('_sy', ty, self.SMOOTH_RISE, self.SMOOTH_FALL),
            ]:
                cur = getattr(self, attr)
                f = rise if abs(target) >= abs(cur) else fall
                setattr(self, attr, cur + (target - cur) * f)

            pitch = max(-self.AXIS_MAX, min(self.AXIS_MAX,
                        int(self._sp) + self._pp))
            roll = max(-self.AXIS_MAX, min(self.AXIS_MAX,
                       int(self._sr) + self._pr))
            yaw = max(-self.AXIS_MAX, min(self.AXIS_MAX,
                      int(self._sy) + self._py))

            self.client.set_pitch(pitch)
            self.client.set_roll(roll)
            self.client.set_yaw(yaw)
            self.client.set_height(self._ph)
            time.sleep(1.0 / self.AXIS_RATE)

    # ========== 按键处理 ==========

    def handle_key(self, key):
        if key is None:
            return True

        # 移动键只记录（轴线程实时检测）
        if key in self.KEYS_MOVEMENT:
            if platform.system() != 'Windows':
                self._mark_key(key)
            return True

        self._last_key = key

        # 退出
        if key == '\x1b':
            self._last_msg = '退出'
            self.running = False
            return False

        # 箭头键 — 姿态微调
        arrow_actions = {
            'ARROW_A': ('_pp', +self.POSTURE_STEP, '俯仰角'),
            'ARROW_B': ('_pp', -self.POSTURE_STEP, '俯仰角'),
            'ARROW_D': ('_pr', -self.POSTURE_STEP, '横滚角'),
            'ARROW_C': ('_pr', +self.POSTURE_STEP, '横滚角'),
        }
        if key in arrow_actions:
            attr, delta, label = arrow_actions[key]
            cur = getattr(self, attr)
            new_val = max(-self.AXIS_MAX, min(self.AXIS_MAX, cur + delta))
            setattr(self, attr, new_val)
            self._last_msg = f'{label} {new_val:+d}'
            return True

        # 分发按键到动作
        if key in self.KEY_ACTIONS:
            action, label = self.KEY_ACTIONS[key]
            self._dispatch_action(action, label)
            return True

        return True

    def _dispatch_action(self, action, label):
        """执行动作并记录消息"""
        actions_map = {
            'stand_toggle':    self.client.stand_toggle,
            'soft_estop':      self.client.soft_estop,
            'zeroing':         self.client.zeroing,
            'in_place_mode':   lambda: (self._reset_axis_inner(),
                                        self.client.set_in_place_mode()),
            'moving_mode':     lambda: (self._reset_axis_inner(),
                                        self.client.set_moving_mode()),
            'manual_mode':     self.client.set_manual_mode,
            'autonomous_mode': self.client.set_autonomous_mode,
            'low_speed_gait':  self.client.set_low_speed_gait,
            'medium_speed_gait': self.client.set_medium_speed_gait,
            'high_speed_gait': self.client.set_high_speed_gait,
            'toggle_crawl':    self.client.toggle_crawl_gait,
            'twist_body':      self.client.twist_body,
            'roll_over':       self.client.roll_over,
            'backflip':        self.client.backflip,
            'greeting':        self.client.greeting,
            'jump_forward':    self.client.jump_forward,
            'twist_jump':      self.client.twist_jump,
            'stop_action':     self.client.stop_action,
            'space_walk':      self.client.space_walk,
            'reset_axis':      self._reset_axis_inner,
            'enter_ai':        self.client.enter_ai,
            'exit_ai':         self.client.exit_ai,
        }
        fn = actions_map[action]
        fn()
        self._last_msg = label

    def _reset_axis_inner(self):
        self._sp = self._sr = self._sy = 0.0
        self._pp = self._pr = self._py = self._ph = 0
        self.client.stop_movement()

    # ========== 渲染 ==========

    @staticmethod
    def _format_duration(elapsed):
        h, rem = divmod(int(elapsed), 3600)
        m, s = divmod(rem, 60)
        if h:
            return f'{h:02d}:{m:02d}:{s:02d}'
        return f'{m:02d}:{s:02d}'

    def _render_top_bar(self, w, elapsed):
        """标题栏 — 单行，带边框"""
        now = time.time()
        with self._stats_lock:
            pkt = self._pkt_count
        # 平均收包速率
        dur = now - self._start_time if self._start_time else 1
        rate = pkt / dur if dur > 0 else 0

        s = self.client.robot_state
        ver = str(s.version) if s else '?'
        err = str(s.error_state) if s else '?'

        dur_s = self._format_duration(elapsed)

        # 左侧信息
        left = f' Lite3 TUI  包:{pkt:<6d} {rate:5.0f}pps  运行:{dur_s}  固件:v{ver} '
        # 右侧错误码
        right = f'err={err} '
        # 中间填充
        inner_w = w - 2
        mid_w = inner_w - _visible_len(left) - _visible_len(right)
        mid = BORDER['h'] * max(1, mid_w)
        return BORDER['tl'] + left + mid + right + BORDER['tr']

    def _render_state_panel(self, w, state):
        """机器人状态面板"""
        if state is None:
            return [
                box_top(w, '机器人状态'),
                box_line(w, c('等待状态数据...', YELLOW)),
                box_bottom(w),
            ]

        bname = state.basic_state_name
        gname = state.gait_state_name
        mname = state.motion_state_name
        batt = state.battery_percentage
        bcolor = CYAN if state.is_standing else YELLOW

        lines = [box_top(w, '机器人状态')]

        # 状态行
        state_col = c(bname, bcolor)
        gait_col = c(gname, CYAN)
        motion_col = c(mname, MAGENTA)
        lines.append(box_line(w,
            f'状态: {_vis_pad(state_col, 14)}  '
            f'步态: {_vis_pad(gait_col, 16)}  '
            f'动作: {_vis_pad(motion_col, 20)}'))

        # 电池行
        b_color = GREEN if batt > 50 else YELLOW if batt > 20 else RED
        lines.append(box_line(w,
            f'电池: {battery_bar(batt)} {c(f"{batt:5.1f}%", b_color)}  '
            f'充电: {"是" if state.is_charging else "否"}'))

        # 策略
        policy = state.policy_state_name if state.policy_state_name else '—'
        lines.append(box_line(w, f'AI策略: {c(policy, BLUE)}'))

        # 标志位
        flags = [
            ('回零', state.zero_position_flag, True),
            ('平衡', not state.is_robot_need_move, True),
            ('AI', state.is_ai_mode, False),
            ('语音', state.is_voice_ctrl_enable, False),
            ('首次', state.is_after_first_start, False),
        ]
        flag_strs = []
        for name, ok, critical in flags:
            if ok:
                fc = GREEN
            elif critical:
                fc = RED
            else:
                fc = DIM
            flag_strs.append(f'{name}:{c("✓" if ok else "✗", fc)}')
        lines.append(box_line(w, '  '.join(flag_strs)))

        lines.append(box_bottom(w))
        return lines

    def _render_imu_panel(self, w, state):
        """IMU 数据面板"""
        if state is None:
            return [
                box_top(w, 'IMU / 传感器'),
                box_line(w, c('等待数据...', YELLOW)),
                box_bottom(w),
            ]

        lines = [box_top(w, 'IMU / 传感器')]

        # 姿态角
        r_color = GREEN if abs(state.roll) < 15 else \
                  YELLOW if abs(state.roll) < 45 else RED
        p_color = GREEN if abs(state.pitch) < 15 else \
                  YELLOW if abs(state.pitch) < 45 else RED
        lines.append(box_line(w,
            f'姿态:  r={c(f"{state.roll:+7.2f}°", r_color)}  '
            f'p={c(f"{state.pitch:+7.2f}°", p_color)}  '
            f'y={state.yaw:+7.2f}°'))

        # 加速度
        g_ok = ' ≈g' if abs(state.z_acc - 9.8) < 1.5 else ''
        lines.append(box_line(w,
            f'加速度: x={state.x_acc:+7.4f}  y={state.y_acc:+7.4f}  '
            f'z={state.z_acc:+7.4f}{g_ok}'))

        # 角速度
        lines.append(box_line(w,
            f'角速度: rr={state.roll_vel:+8.5f}  pr={state.pitch_vel:+8.5f}  '
            f'yr={state.yaw_vel:+8.5f}'))

        # 超声波 — 近距离红色告警
        us_f = state.ultrasound_forward
        us_b = state.ultrasound_backward
        us_fc = RED if us_f < 0.5 else WHITE
        us_bc = RED if us_b < 0.5 else WHITE
        lines.append(box_line(w,
            f'超声波: 前={c(f"{us_f:.2f}m", us_fc)}  '
            f'后={c(f"{us_b:.2f}m", us_bc)}'))

        lines.append(box_bottom(w))
        return lines

    def _render_pose_panel(self, w, state):
        """位姿 / 速度面板"""
        if state is None:
            return [
                box_top(w, '位姿 / 速度'),
                box_line(w, c('等待数据...', YELLOW)),
                box_bottom(w),
            ]

        lines = [box_top(w, '位姿 / 速度')]

        lines.append(box_line(w,
            f'世界坐标: x={state.pos_x:+8.3f}m  y={state.pos_y:+8.3f}m  '
            f'yaw={state.pos_yaw:+8.4f}rad'))

        lines.append(box_line(w,
            f'世界速度: x={state.vel_x_world:+8.4f}  y={state.vel_y_world:+8.4f}  '
            f'yaw={state.vel_yaw_world:+8.4f}'))

        lines.append(box_line(w,
            f'身体速度: x={state.vel_x_body:+8.4f}  y={state.vel_y_body:+8.4f}  '
            f'yaw={state.vel_yaw_body:+8.4f}'))

        lines.append(box_bottom(w))
        return lines

    def _render_axis_panel(self, w):
        """轴指令面板 — 含双向进度条"""
        pitch = int(self._sp) + self._pp
        roll = int(self._sr) + self._pr
        yaw = int(self._sy) + self._py

        lines = [box_top(w, '轴指令')]

        for label, val in [('pitch', pitch), ('roll', roll), ('yaw', yaw)]:
            vcolor = GREEN if abs(val) < 100 else YELLOW
            lines.append(box_line(w,
                f'{label:<6s} {bar(val)} {c(f"{val:+6d}", vcolor)}'))

        lines.append(box_line(w, f'height {" " * 4}{c(f"{self._ph:+6d}", CYAN)}'))
        lines.append(box_bottom(w))
        return lines

    def _render_key_panel(self, w):
        """按键状态面板"""
        kw = self._is_movement_held('w'); ks = self._is_movement_held('s')
        ka = self._is_movement_held('a'); kd = self._is_movement_held('d')
        kq = self._is_movement_held('q'); ke = self._is_movement_held('e')

        lines = [box_top(w, '按键')]

        lines.append(box_line(w,
            f'{key_indicator("W",kw)}前进 {key_indicator("S",ks)}后退  '
            f'{key_indicator("A",ka)}左转 {key_indicator("D",kd)}右转'))

        lines.append(box_line(w,
            f'{key_indicator("Q",kq)}左移 {key_indicator("E",ke)}右移  '
            f'│  箭头键:姿态  {c("h", CYAN)}:重置'))

        lines.append(box_bottom(w))
        return lines

    def _render_shortcuts(self, w):
        """快捷键面板"""
        lines = [box_top(w, '快捷键')]

        lines.append(box_line(w,
            f'模式: {c("1",CYAN)}原地 {c("2",CYAN)}移动 {c("3",CYAN)}手动 {c("4",CYAN)}自主 │ '
            f'基本: {c("空格",YELLOW)}起立 {c("r",YELLOW)}急停 {c("z",YELLOW)}回零 │ '
            f'{c("a",MAGENTA)}AI {c("x",MAGENTA)}退AI'))

        lines.append(box_line(w,
            f'步态: {c("u",CYAN)}低速 {c("i",CYAN)}中速 {c("o",CYAN)}高速 {c("l",CYAN)}匍匐 │ '
            f'动作: {c("t",YELLOW)}扭 {c("f",YELLOW)}翻 {c("p",YELLOW)}太空 '
            f'{c("b",YELLOW)}后翻 {c("g",YELLOW)}招呼 {c("j",YELLOW)}跳 {c("y",YELLOW)}扭跳 '
            f'{c("c",YELLOW)}停'))

        lines.append(box_line(w, f'{c("ESC",RED)} 退出'))
        lines.append(box_bottom(w))
        return lines

    def _render_frame(self):
        """构建完整帧 — 单字符串，单次写入减少撕裂"""
        tw, th = term_size()
        w = min(tw, 100)  # 最大 100 列，过宽可读性差
        elapsed = time.time() - self._start_time if self._start_time else 0
        state = self.client.robot_state

        lines = []

        # ── 标题栏 ──
        lines.append(self._render_top_bar(w, elapsed))

        # ── 上半部分：状态面板 + 轴指令面板 (并排) ──
        if w >= 80:
            left_w = max(36, (w - 3) * 55 // 100)
            right_w = w - left_w - 1

            state_lines = self._render_state_panel(left_w, state)
            axis_lines = self._render_axis_panel(right_w)

            max_h = max(len(state_lines), len(axis_lines))
            for i in range(max_h):
                sl = state_lines[i] if i < len(state_lines) else ' ' * left_w
                al = axis_lines[i] if i < len(axis_lines) else ' ' * right_w
                lines.append(sl + ' ' + al)
        else:
            lines.extend(self._render_state_panel(w, state))
            lines.append('')
            lines.extend(self._render_axis_panel(w))

        lines.append('')

        # ── 中部：IMU 面板 + 按键面板 (并排) ──
        if w >= 80:
            left_w = max(40, (w - 3) * 55 // 100)
            right_w = w - left_w - 1

            imu_lines = self._render_imu_panel(left_w, state)
            key_lines = self._render_key_panel(right_w)

            max_h = max(len(imu_lines), len(key_lines))
            for i in range(max_h):
                il = imu_lines[i] if i < len(imu_lines) else ' ' * left_w
                kl = key_lines[i] if i < len(key_lines) else ' ' * right_w
                lines.append(il + ' ' + kl)
        else:
            lines.extend(self._render_imu_panel(w, state))
            lines.append('')
            lines.extend(self._render_key_panel(w))

        lines.append('')

        # ── 下半部分：位姿面板 ──
        lines.extend(self._render_pose_panel(w, state))
        lines.append('')

        # ── 快捷键面板 ──
        lines.extend(self._render_shortcuts(w))

        # ── 操作反馈行 ──
        if self._last_msg:
            lines.append('')
            msg = c(f' >>> {self._last_msg}', GREEN + ';' + BOLD)
            lines.append(_vis_pad(msg, w))

        return '\n'.join(lines)

    # ========== 主循环 ==========

    def run(self):
        if not self.connect():
            print("连接失败！")
            return

        self._start_axis()
        self.running = True
        self._start_time = time.time()

        setup_terminal()
        # 清屏一次
        sys.stdout.write('\033[2J')
        sys.stdout.flush()

        try:
            while self.running:
                key = getch()
                if not self.handle_key(key):
                    break

                # 构建完整帧，单次写入（最小化撕裂）
                frame = self._render_frame()
                sys.stdout.write('\033[H')
                sys.stdout.write(frame)
                sys.stdout.write('\033[J')  # 清除尾部残留
                sys.stdout.flush()

                time.sleep(0.02 if platform.system() == 'Windows' else 0.05)

        except KeyboardInterrupt:
            pass
        finally:
            restore_terminal()
            sys.stdout.write('\033[2J\033[H')
            self.disconnect()
            elapsed = time.time() - self._start_time if self._start_time else 0
            dur_s = self._format_duration(elapsed)
            print(f"已退出。运行时长: {dur_s}  收包: {self._pkt_count}")


# =============================================================================
# 入口
# =============================================================================

def main():
    parser = argparse.ArgumentParser(description='Lite3 机器人键盘控制 — TUI 版本')
    parser.add_argument('--host', default='192.168.0.37', help='运动主机 IP')
    parser.add_argument('--port', type=int, default=43893, help='运动主机端口')
    parser.add_argument('--local-port', type=int, default=43897, help='本机绑定端口')
    args = parser.parse_args()

    controller = TuiController(args.host, args.port, args.local_port)
    controller.run()


if __name__ == '__main__':
    main()
