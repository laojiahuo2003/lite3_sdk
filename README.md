# Lite3 机器人 SDK

绝影 Lite3 四足机器人运动控制 Python SDK，通过 UDP 协议与运动主机通信，支持完整的运动控制、状态监控及摄像头视频流接入。

[![Python](https://img.shields.io/badge/python-≥3.10-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green)](./LICENSE)

## 功能特性

- **完整指令覆盖** — 40+ 种控制指令：运动控制、状态切换、步态/越障切换、AI 模式、动作、语音/扬声器
- **UDP 通信封装** — 简单指令 / 复杂指令自动封包，响应对端解析
- **实时状态解析** — 机器人状态(IMU/位姿/速度/电池/超声波)、12 关节角度、12 关节角速度
- **自动心跳** — 后台线程维持心跳，频率可配（≥2 Hz）
- **异步回调** — 状态/关节数据到达时自动回调，无需轮询
- **摄像头接入** — RTSP 视频流客户端，支持阻塞/非阻塞读取、帧回调
- **上下文管理器** — `with` 语句自动 connect/disconnect
- **键盘控制示例** — 开箱即用的键盘遥控脚本

## 系统要求

- Python **≥ 3.10**
- 依赖：[numpy](https://pypi.org/project/numpy/) ≥ 1.24、[opencv-python-headless](https://pypi.org/project/opencv-python-headless/) ≥ 4.5.0（仅摄像头功能需要）

## 安装

```bash
cd lite3_sdk
pip install -e .
```

## 快速开始

### 连接与基础控制

```python
from lite3_sdk import Lite3Client

client = Lite3Client(host="192.168.1.120", port=43893)

# verify=True 会发送心跳包验证目标是否可达（推荐）
if not client.connect(verify=True):
    print("连接失败，请检查机器狗是否开机")
    return

client.start_heartbeat(rate=5.0)   # 启动心跳（必须）

client.stand_toggle()              # 起立 / 趴下
client.set_moving_mode()           # 移动模式
client.set_pitch(10000)            # 向前移动

client.disconnect()
```

### 上下文管理器（推荐）

```python
with Lite3Client(host="192.168.1.120") as client:
    client.start_heartbeat()
    client.stand_toggle()
    # ... 其他操作
    # 退出 with 块自动断开连接
```

### 状态监控

```python
def on_state(state):
    print(f"电池: {state.battery_percentage:.1f}%  "
          f"位置: ({state.pos_x:.2f}, {state.pos_y:.2f})")

with Lite3Client() as client:
    client.start_heartbeat()
    client.set_robot_state_callback(on_state)
    time.sleep(10)
```

### 摄像头视频流

```python
from lite3_sdk import CameraClient

camera = CameraClient(host="192.168.2.1")

if camera.connect():
    while True:
        frame = camera.read_frame()
        if frame is not None:
            cv2.imshow("Camera", frame)
            if cv2.waitKey(1) & 0xFF in (ord('q'), 27):
                break
    camera.disconnect()
```

## 指令速查

### 状态转换

| 方法 | 说明 |
|------|------|
| `stand_toggle()` | 起立 / 趴下切换 |
| `soft_estop()` | 软急停 |
| `zeroing()` | 回零 |
| `enter_ai()` | 进入 AI 模式 |
| `exit_ai()` | 退出 AI 模式 |

### 模式切换

| 方法 | 说明 |
|------|------|
| `set_in_place_mode()` | 原地模式 |
| `set_moving_mode()` | 移动模式 |
| `set_autonomous_mode()` | 自主模式（速度指令生效） |
| `set_manual_mode()` | 手动模式（轴指令生效） |

### 轴指令（手柄 / 移动模式）

| 方法 | 范围 | 说明 |
|------|------|------|
| `set_roll(value)` | [-32767, 32767] | 横滚角 / 左右平移 |
| `set_pitch(value)` | [-32767, 32767] | 俯仰角 / 前后平移 |
| `set_height(value)` | [-20000, 20000] | 身体高度 |
| `set_yaw(value)` | [-32767, 32767] | 偏航角 / 左右转弯 |

### 速度指令（仅自主模式有效）

| 方法 | 范围 | 单位 | 说明 |
|------|------|------|------|
| `set_x_velocity(v)` | [-1.0, 1.0] | m/s | 前后平移 |
| `set_y_velocity(v)` | [-0.5, 0.5] | m/s | 左右平移 |
| `set_yaw_velocity(v)` | [-1.5, 1.5] | rad/s | 旋转速度 |

### 步态切换

| 方法 | 说明 |
|------|------|
| `set_low_speed_gait()` | 平地低速步态 |
| `set_medium_speed_gait()` | 平地中速步态 |
| `set_high_speed_gait()` | 平地高速步态 |
| `toggle_crawl_gait()` | 正常 / 匍匐步态切换 |
| `set_grip_obstacle_gait()` | 抓地越障步态 |
| `set_general_obstacle_gait()` | 通用越障步态 |
| `set_high_step_obstacle_gait()` | 高踏步越障步态 |

### 动作指令

| 方法 | 说明 |
|------|------|
| `twist_body()` | 扭身体 |
| `roll_over()` | 翻身 |
| `space_walk()` | 太空步 |
| `backflip()` | 后空翻 |
| `greeting()` | 打招呼 |
| `jump_forward()` | 向前跳 |
| `twist_jump()` | 扭身跳 |
| `stop_action()` | 停止动作 |

### AI 相关

| 方法 | 说明 |
|------|------|
| `set_ai_basic_gait()` | AI 基础步态 |
| `set_ai_jump_gait()` | AI 跳跃步态 |
| `set_ai_stand_gait()` | AI 站立步态 |
| `set_ai_high_speed_gait()` | AI 极速步态 |
| `perform_ai_action(value)` | 执行 AI 动作 |
| `set_continuous_motion(enable)` | AI 持续运动开关 |
| `set_ai_settings(value)` | AI 选项 |

### 其他

| 方法 | 说明 |
|------|------|
| `send_voice_command(value)` | 语音指令 |
| `control_speaker(value)` | 扬声器控制 |
| `stop_movement()` | 停止所有轴运动（发送全部轴值为 0） |
| `save_data()` | 保存数据 |

## 摄像头客户端

[CameraClient](lite3_sdk/camera_client.py) 通过 RTSP 协议连接 Lite3 运动主机上的摄像头。

| 方法 | 说明 |
|------|------|
| `connect(timeout)` | 连接 RTSP 视频流，默认超时 10s |
| `read_frame()` | 读取一帧（阻塞），返回 `np.ndarray` 或 `None` |
| `get_latest_frame()` | 获取最新帧（非阻塞），线程安全 |
| `set_frame_callback(fn)` | 设置帧回调，签名 `fn(frame: np.ndarray)` |
| `start_receiving()` | 启动异步接收线程 |
| `stop_receiving()` | 停止异步接收 |
| `get_frame_info()` | 获取 `(宽, 高, 帧率)` 或 `None` |
| `disconnect()` | 断开连接 |

## 数据模型

### [RobotState](lite3_sdk/models/robot_state.py)

通过 `client.robot_state` 获取最新状态，或注册回调 `client.set_robot_state_callback(fn)`。

| 属性 | 类型 | 说明 |
|------|------|------|
| `robot_basic_state` | `int` | 基本运动状态（见 `RobotBasicState` 枚举） |
| `robot_gait_state` | `int` | 当前步态（见 `RobotGaitState` 枚举） |
| `robot_policy_state` | `int` | AI 步态（见 `RobotPolicyState` 枚举） |
| `robot_motion_state` | `int` | 动作状态（见 `RobotMotionState` 枚举） |
| `roll` / `pitch` / `yaw` | `float` | IMU 姿态角 (°) |
| `roll_vel` / `pitch_vel` / `yaw_vel` | `float` | IMU 角速度 (rad/s) |
| `x_acc` / `y_acc` / `z_acc` | `float` | IMU 加速度 (m/s²) |
| `pos_x` / `pos_y` / `pos_yaw` | `float` | 世界坐标位置 (m) 和偏航角 (rad) |
| `vel_x_world` / `vel_y_world` / `vel_yaw_world` | `float` | 世界坐标系速度 |
| `vel_x_body` / `vel_y_body` / `vel_yaw_body` | `float` | 身体坐标系速度 |
| `battery_level` | `float` | 电池电量小数（0~1） |
| `ultrasound_forward` / `ultrasound_backward` | `float` | 超声波障碍物距离 (m) |
| `is_robot_need_move` | `bool` | 受外力影响的平衡状态 |
| `is_voice_ctrl_enable` | `bool` | 语音控制是否开启 |

计算属性：

| 属性 | 说明 |
|------|------|
| `battery_percentage` | `battery_level * 100` |
| `is_standing` | 是否处于站立状态（FORCE_CONTROL 或 AI_STATE） |
| `is_ai_mode` | 是否处于 AI 模式 |
| `basic_state_name` | 基本状态名（如 `"FORCE_CONTROL"`） |
| `gait_state_name` | 步态名 |
| `policy_state_name` | AI 步态名 |
| `motion_state_name` | 动作状态名 |

### [JointAngles](lite3_sdk/models/joints.py) / [JointVelocities](lite3_sdk/models/joints.py)

12 个关节的角度 (rad) 和角速度 (rad/s)，通过 `client.joint_angles` / `client.joint_velocities` 获取。

| 属性 | 说明 |
|------|------|
| `left_front_abduction` ~ `right_back_knee` | 各关节逐一命名的访问器 |
| `joint_angles` / `joint_velocities` | `List[float]`，12 个值按关节编号排列 |

### 回调注册

```python
client.set_robot_state_callback(callback)       # callback(state: RobotState)
client.set_joint_angles_callback(callback)      # callback(angles: JointAngles)
client.set_joint_velocities_callback(callback)  # callback(velocities: JointVelocities)
client.set_speaker_state_callback(callback)     # callback(state: int)  # 0=关闭, 1=开启
```

## UDP 连接验证说明

UDP 是无连接协议，默认 `connect()` 只创建 socket，不验证目标是否可达。本 SDK 提供两种方式：

| 方式 | 行为 |
|------|------|
| `connect(verify=True)` | 发送心跳包并等待响应，目标不可达时返回失败 |
| `connect(verify=False)` | 只创建 socket，不验证可达性 |

> **建议**：开发调试时使用 `verify=True` 尽早发现网络问题；不确定机器狗状态时可先用 `verify=False`。

## 示例代码

| 示例 | 文件 | 说明 |
|------|------|------|
| 基础用法 | [examples/basic_usage.py](examples/basic_usage.py) | 连接、心跳、模式切换、AI 模式、自主模式、动作、状态监控 |
| 起立趴下 | [examples/stand_sit_demo.py](examples/stand_sit_demo.py) | 起立/趴下切换 + 状态等待 |
| 键盘遥控 | [examples/keyboard_control.py](examples/keyboard_control.py) | 全功能键盘控制，支持所有指令 |
| 摄像头 | [examples/camera_demo.py](examples/camera_demo.py) | RTSP 视频流实时显示 |
| 连接测试 | [test_connection.py](test_connection.py) | ping + verify 连接诊断 |
| SDK 验证 | [verify_sdk.py](verify_sdk.py) | 离线功能验证，无需机器人 |

## 注意事项

| # | 说明 |
|---|------|
| 1 | **心跳必须启动**，频率不低于 2 Hz，否则运动会自动停止 |
| 2 | **轴指令频率** ≥ 20 Hz，超时 250ms 后运动自动停止（SDK 内部不自动重发，高频控制请在应用层循环发送） |
| 3 | **速度指令**（`set_x_velocity` / `set_y_velocity` / `set_yaw_velocity`）仅在自主模式下有效 |
| 4 | AI 状态下，部分运动控制指令可能被忽略 |
| 5 | 运动主机默认 IP 为 `192.168.1.120`，需正确配置网络（直连或同网段） |
| 6 | 摄像头 IP 通常与运动主机 IP 不同（默认 `192.168.2.1`），RTSP 端口为 `8554` |

## 项目结构

```
lite3_sdk/
├── lite3_sdk/
│   ├── __init__.py          # 公开 API 导出
│   ├── client.py            # Lite3Client 运动控制客户端
│   ├── camera_client.py     # CameraClient RTSP 视频流客户端
│   ├── commands/            # 指令定义
│   │   ├── base.py          # SimpleCommand / ComplexCommand 基类
│   │   ├── command_codes.py # CommandCode 枚举 (30+ 指令码)
│   │   ├── gait_action.py   # 步态 / 动作 / AI / 语音指令
│   │   ├── motion.py        # 运动控制指令
│   │   └── state.py         # 状态转换指令
│   ├── models/
│   │   ├── robot_state.py   # RobotState + 状态枚举
│   │   └── joints.py        # JointAngles / JointVelocities
│   └── network/
│       ├── udp_client.py    # UDP 底层通信
│       └── message_parser.py # 响应消息解析
├── examples/                # 使用示例
├── tests/                   # 单元测试
└── pyproject.toml
```

## 许可证

MIT License
