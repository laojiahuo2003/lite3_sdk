# Lite3机器人SDK

Lite3机器人运动控制SDK，用于通过UDP协议与绝影Lite3运动主机通信。

## 功能特性

- ✅ 完整的UDP通信封装
- ✅ 所有控制指令支持（30+种指令）
- ✅ 机器人状态数据解析
- ✅ 关节角度和角速度数据解析
- ✅ 自动心跳机制
- ✅ 异步数据接收和回调
- ✅ 简洁易用的API

## 安装

```bash
cd lite3_sdk
pip install -e .
```

## 快速开始

### 基础使用

```python
from lite3_sdk import Lite3Client

# 创建客户端
client = Lite3Client(host="192.168.1.120", port=43893)

# 连接（verify=True会验证目标主机是否可达）
# 如果机器狗未开机，连接会失败
if not client.connect(verify=True):
    print("连接失败，请检查机器狗是否开机")
    return

# 启动心跳（必须）
client.start_heartbeat(rate=5.0)

# 控制机器人
client.stand_toggle()  # 起立/趴下
client.set_moving_mode()  # 移动模式
client.set_pitch(10000)  # 向前移动

# 断开连接
client.disconnect()
```

### 重要说明：UDP连接验证

**UDP是无连接协议**，默认情况下即使目标主机不可达，`connect()`也会返回成功。

本SDK提供两种连接方式：

1. **验证连接（推荐）**：`client.connect(verify=True)`
   - 发送心跳包并等待响应
   - 如果机器狗未开机或网络不通，会返回失败
   - 需要机器狗已配置数据上报（参考文档第4节）

2. **不验证连接**：`client.connect(verify=False)`
   - 只创建socket，不验证目标可达性
   - 适用于不确定机器狗状态的情况
   - 发送指令可能失败，但不会立即报错

### 使用上下文管理器

```python
from lite3_sdk import Lite3Client

with Lite3Client(host="192.168.1.120") as client:
    client.start_heartbeat()
    
    # 控制机器人
    client.stand_toggle()
    # ... 其他操作
```

### 监控机器人状态

```python
def state_callback(state):
    print(f"电池: {state.battery_percentage:.1f}%")
    print(f"位置: ({state.pos_x:.2f}, {state.pos_y:.2f})")

with Lite3Client() as client:
    client.start_heartbeat()
    client.set_robot_state_callback(state_callback)
    
    # 等待接收数据
    time.sleep(10)
```

## 主要API

### 状态转换

- `stand_toggle()` - 起立/趴下切换
- `soft_estop()` - 软急停
- `zeroing()` - 回零
- `enter_ai()` - 进入AI模式
- `exit_ai()` - 退出AI模式

### 运动模式

- `set_in_place_mode()` - 原地模式
- `set_moving_mode()` - 移动模式

### 控制模式

- `set_autonomous_mode()` - 自主模式
- `set_manual_mode()` - 手动模式

### 轴指令（手柄控制）

- `set_roll(value)` - 横滚角/左右平移
- `set_pitch(value)` - 俯仰角/前后平移
- `set_height(value)` - 身体高度
- `set_yaw(value)` - 偏航角/左右转弯

### 速度指令（自主模式）

- `set_x_velocity(velocity)` - 前后平移速度
- `set_y_velocity(velocity)` - 左右平移速度
- `set_yaw_velocity(velocity)` - 旋转角速度

### 步态切换

- `set_low_speed_gait()` - 低速步态
- `set_medium_speed_gait()` - 中速步态
- `set_high_speed_gait()` - 高速步态
- `set_grip_obstacle_gait()` - 抓地越障步态
- `set_general_obstacle_gait()` - 通用越障步态

### 动作指令

- `twist_body()` - 扭身体
- `roll_over()` - 翻身
- `space_walk()` - 太空步
- `backflip()` - 后空翻
- `greeting()` - 打招呼
- `jump_forward()` - 向前跳

### AI相关

- `set_ai_basic_gait()` - AI基础步态
- `set_ai_jump_gait()` - AI跳跃步态
- `set_ai_stand_gait()` - AI站立步态
- `perform_ai_action(value)` - AI动作

## 数据模型

### RobotState

机器人状态信息，包含：
- 基本运动状态
- 步态状态
- AI步态状态
- IMU数据（角度、角速度、加速度）
- 世界坐标系位置和速度
- 身体坐标系速度
- 电池电量
- 超声波距离

### JointAngles

12个关节的角度信息（单位：rad）

### JointVelocities

12个关节的角速度信息（单位：rad/s）

## 注意事项

1. **心跳必须启动**：频率应不低于2Hz
2. **轴指令频率**：应不低于20Hz，超时250ms自动停止
3. **自主模式**：速度指令仅在自主模式下有效
4. **AI状态限制**：某些指令在AI状态下无效
5. **网络配置**：需要正确配置运动主机IP地址

## 示例代码

查看 `examples/basic_usage.py` 获取更多使用示例。

## 许可证

MIT License