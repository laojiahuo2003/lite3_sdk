"""Lite3机器人SDK主客户端"""
import time
import threading
from typing import Optional, Callable
from .network import UDPClient, MessageParser
from .models import RobotState, JointAngles, JointVelocities
from .commands import (
    BaseCommand,
    HeartbeatCommand,
    RollCommand,
    PitchCommand,
    HeightCommand,
    YawCommand,
    YawVelocityCommand,
    XVelocityCommand,
    YVelocityCommand,
    StandToggleCommand,
    SoftEstopCommand,
    ZeroingCommand,
    EnterAICommand,
    ExitAICommand,
    InPlaceModeCommand,
    MovingModeCommand,
    AutonomousModeCommand,
    ManualModeCommand,
    LowSpeedGaitCommand,
    MediumSpeedGaitCommand,
    HighSpeedGaitCommand,
    CrawlToggleCommand,
    GripObstacleGaitCommand,
    GeneralObstacleGaitCommand,
    HighStepObstacleGaitCommand,
    TwistBodyCommand,
    RollOverCommand,
    SpaceWalkCommand,
    BackflipCommand,
    GreetingCommand,
    JumpForwardCommand,
    TwistJumpCommand,
    StopActionCommand,
    VoiceCommand,
    SpeakerCommand,
    AISettingsCommand,
    ContinuousMotionCommand,
    AIBasicGaitCommand,
    AIJumpGaitCommand,
    AIStandGaitCommand,
    AIHighSpeedGaitCommand,
    AIActionCommand,
    SaveDataCommand,
    CommandCode,
    VoiceCommandValue,
    AISettingsValue,
    AIActionValue,
    SpeakerValue
)


class Lite3Client:
    """Lite3机器人客户端"""

    def __init__(self, host: str = "192.168.1.120", port: int = 43893, timeout: float = 1.0,
                 packet_log_path: str = None, local_port: int = 0):
        self.host = host
        self.port = port
        self.timeout = timeout
        self._verify = True
        self.udp_client = UDPClient(host, port, timeout,
                                    packet_log_path=packet_log_path,
                                    local_port=local_port)

        self._robot_state: Optional[RobotState] = None
        self._joint_angles: Optional[JointAngles] = None
        self._joint_velocities: Optional[JointVelocities] = None

        # 回调函数
        self._robot_state_callback: Optional[Callable[[RobotState], None]] = None
        self._joint_angles_callback: Optional[Callable[[JointAngles], None]] = None
        self._joint_velocities_callback: Optional[Callable[[JointVelocities], None]] = None
        self._speaker_state_callback: Optional[Callable[[int], None]] = None

        # 心跳线程
        self._heartbeat_thread: Optional[threading.Thread] = None
        self._heartbeat_running = False
        self._heartbeat_rate = 5.0  # 默认5Hz

        # 注册消息处理器
        self._register_message_handlers()

    def _register_message_handlers(self):
        """注册消息处理器"""
        self.udp_client.register_handler(
            CommandCode.RECV_ROBOT_STATE,
            self._handle_robot_state
        )
        self.udp_client.register_handler(
            CommandCode.RECV_JOINT_ANGLE,
            self._handle_joint_angles
        )
        self.udp_client.register_handler(
            CommandCode.RECV_JOINT_VELOCITY,
            self._handle_joint_velocities
        )
        self.udp_client.register_handler(
            CommandCode.RECV_SPEAKER_STATE,
            self._handle_speaker_state
        )

    def _handle_robot_state(self, code: int, data: bytes):
        """处理机器人状态消息"""
        robot_state = MessageParser.parse_robot_state(data)
        if robot_state:
            self._robot_state = robot_state
            if self._robot_state_callback:
                try:
                    self._robot_state_callback(robot_state)
                except Exception as e:
                    print(f"机器人状态回调函数执行失败: {e}")

    def _handle_joint_angles(self, code: int, data: bytes):
        """处理关节角度消息"""
        joint_angles = MessageParser.parse_joint_angles(data)
        if joint_angles:
            self._joint_angles = joint_angles
            if self._joint_angles_callback:
                try:
                    self._joint_angles_callback(joint_angles)
                except Exception as e:
                    print(f"关节角度回调函数执行失败: {e}")

    def _handle_joint_velocities(self, code: int, data: bytes):
        """处理关节角速度消息"""
        joint_velocities = MessageParser.parse_joint_velocities(data)
        if joint_velocities:
            self._joint_velocities = joint_velocities
            if self._joint_velocities_callback:
                try:
                    self._joint_velocities_callback(joint_velocities)
                except Exception as e:
                    print(f"关节角速度回调函数执行失败: {e}")

    def _handle_speaker_state(self, code: int, data: bytes):
        """处理扬声器状态消息（0=关闭, 1=开启）"""
        if len(data) >= 4:
            state = int.from_bytes(data[:4], 'little')
            if self._speaker_state_callback:
                try:
                    self._speaker_state_callback(state)
                except Exception as e:
                    print(f"扬声器状态回调函数执行失败: {e}")

    def connect(self, verify: bool = True) -> bool:
        self._verify = verify
        if not self.udp_client.connect(verify=verify):
            return False
        self.udp_client.start_receiving()
        return True

    def disconnect(self):
        """断开连接"""
        self.stop_heartbeat()
        self.udp_client.disconnect()

    def send_command(self, command: BaseCommand) -> bool:
        """
        发送指令

        Args:
            command: 指令对象

        Returns:
            是否发送成功
        """
        code, parameters_size, data = command.get_command_data()

        if data:
            return self.udp_client.send_complex_command(code, data)
        else:
            return self.udp_client.send_simple_command(code, parameters_size)

    # ========== 心跳相关 ==========

    def start_heartbeat(self, rate: float = 5.0):
        """
        启动心跳

        Args:
            rate: 心跳频率(Hz)，应不低于2Hz
        """
        if self._heartbeat_running:
            return

        self._heartbeat_rate = max(2.0, rate)
        self._heartbeat_running = True
        self._heartbeat_thread = threading.Thread(target=self._heartbeat_loop, daemon=True)
        self._heartbeat_thread.start()

    def stop_heartbeat(self):
        """停止心跳"""
        self._heartbeat_running = False
        if self._heartbeat_thread:
            self._heartbeat_thread.join(timeout=2.0)
            self._heartbeat_thread = None

    def _heartbeat_loop(self):
        """心跳循环"""
        command = HeartbeatCommand()
        while self._heartbeat_running:
            self.send_command(command)
            time.sleep(1.0 / self._heartbeat_rate)

    # ========== 状态转换 ==========

    def stand_toggle(self) -> bool:
        """起立/趴下切换"""
        return self.send_command(StandToggleCommand())

    def soft_estop(self) -> bool:
        """软急停"""
        return self.send_command(SoftEstopCommand())

    def zeroing(self) -> bool:
        """回零"""
        return self.send_command(ZeroingCommand())

    def enter_ai(self) -> bool:
        """进入AI模式"""
        return self.send_command(EnterAICommand())

    def exit_ai(self) -> bool:
        """退出AI模式"""
        return self.send_command(ExitAICommand())

    # ========== 运动模式 ==========

    def set_in_place_mode(self) -> bool:
        """设置原地模式"""
        return self.send_command(InPlaceModeCommand())

    def set_moving_mode(self) -> bool:
        """设置移动模式"""
        return self.send_command(MovingModeCommand())

    # ========== 控制模式 ==========

    def set_autonomous_mode(self) -> bool:
        """设置自主模式"""
        return self.send_command(AutonomousModeCommand())

    def set_manual_mode(self) -> bool:
        """设置手动模式"""
        return self.send_command(ManualModeCommand())

    # ========== 轴指令 ==========

    def set_roll(self, value: int) -> bool:
        """
        设置横滚角/左右平移

        Args:
            value: 轴值，范围[-32767, 32767]
        """
        return self.send_command(RollCommand(value))

    def set_pitch(self, value: int) -> bool:
        """
        设置俯仰角/前后平移

        Args:
            value: 轴值，范围[-32767, 32767]
        """
        return self.send_command(PitchCommand(value))

    def set_height(self, value: int) -> bool:
        """
        设置身体高度

        Args:
            value: 轴值，范围[-20000, 20000]
        """
        return self.send_command(HeightCommand(value))

    def set_yaw(self, value: int) -> bool:
        """
        设置偏航角/左右转弯

        Args:
            value: 轴值，范围[-32767, 32767]
        """
        return self.send_command(YawCommand(value))

    # ========== 速度指令（自主模式） ==========

    def set_yaw_velocity(self, velocity: float) -> bool:
        """
        设置旋转角速度（自主模式）

        Args:
            velocity: 旋转角速度(rad/s)，范围[-1.5, 1.5]
        """
        return self.send_command(YawVelocityCommand(velocity))

    def set_x_velocity(self, velocity: float) -> bool:
        """
        设置前后平移速度（自主模式）

        Args:
            velocity: 前后平移速度(m/s)，范围[-1.0, 1.0]
        """
        return self.send_command(XVelocityCommand(velocity))

    def set_y_velocity(self, velocity: float) -> bool:
        """
        设置左右平移速度（自主模式）

        Args:
            velocity: 左右平移速度(m/s)，范围[-0.5, 0.5]
        """
        return self.send_command(YVelocityCommand(velocity))

    # ========== 步态切换 ==========

    def set_low_speed_gait(self) -> bool:
        """设置平地低速步态"""
        return self.send_command(LowSpeedGaitCommand())

    def set_medium_speed_gait(self) -> bool:
        """设置平地中速步态"""
        return self.send_command(MediumSpeedGaitCommand())

    def set_high_speed_gait(self) -> bool:
        """设置平地高速步态"""
        return self.send_command(HighSpeedGaitCommand())

    def toggle_crawl_gait(self) -> bool:
        """切换正常/匍匐步态"""
        return self.send_command(CrawlToggleCommand())

    def set_grip_obstacle_gait(self) -> bool:
        """设置抓地越障步态"""
        return self.send_command(GripObstacleGaitCommand())

    def set_general_obstacle_gait(self) -> bool:
        """设置通用越障步态"""
        return self.send_command(GeneralObstacleGaitCommand())

    def set_high_step_obstacle_gait(self) -> bool:
        """设置高踏步越障步态"""
        return self.send_command(HighStepObstacleGaitCommand())

    # ========== 动作指令 ==========

    def twist_body(self) -> bool:
        """扭身体"""
        return self.send_command(TwistBodyCommand())

    def roll_over(self) -> bool:
        """翻身"""
        return self.send_command(RollOverCommand())

    def space_walk(self) -> bool:
        """太空步"""
        return self.send_command(SpaceWalkCommand())

    def backflip(self) -> bool:
        """后空翻"""
        return self.send_command(BackflipCommand())

    def greeting(self) -> bool:
        """打招呼"""
        return self.send_command(GreetingCommand())

    def jump_forward(self) -> bool:
        """向前跳"""
        return self.send_command(JumpForwardCommand())

    def twist_jump(self) -> bool:
        """扭身跳"""
        return self.send_command(TwistJumpCommand())

    def stop_action(self) -> bool:
        """停止动作（文档要求同时发送指令值 0 和 1）"""
        cmd0 = StopActionCommand()  # 指令值 0
        cmd1 = StopActionCommand(value=1)  # 指令值 1
        return self.send_command(cmd0) and self.send_command(cmd1)

    # ========== 语音和扬声器 ==========

    def send_voice_command(self, value: VoiceCommandValue) -> bool:
        """
        发送语音指令

        Args:
            value: 语音指令值
        """
        return self.send_command(VoiceCommand(value))

    def control_speaker(self, value: SpeakerValue) -> bool:
        """
        控制扬声器

        Args:
            value: 扬声器指令值
        """
        return self.send_command(SpeakerCommand(value))

    # ========== AI相关 ==========

    def set_ai_settings(self, value: AISettingsValue) -> bool:
        """
        设置AI选项

        Args:
            value: AI设置值
        """
        return self.send_command(AISettingsCommand(value))

    def set_continuous_motion(self, enable: bool) -> bool:
        """
        设置持续运动

        Args:
            enable: True开启，False关闭
        """
        return self.send_command(ContinuousMotionCommand(enable))

    def set_ai_basic_gait(self) -> bool:
        """设置AI基础步态"""
        return self.send_command(AIBasicGaitCommand())

    def set_ai_jump_gait(self) -> bool:
        """设置AI跳跃步态"""
        return self.send_command(AIJumpGaitCommand())

    def set_ai_stand_gait(self) -> bool:
        """设置AI站立步态"""
        return self.send_command(AIStandGaitCommand())

    def set_ai_high_speed_gait(self) -> bool:
        """设置AI极速步态"""
        return self.send_command(AIHighSpeedGaitCommand())

    def perform_ai_action(self, value: AIActionValue) -> bool:
        """
        执行AI动作

        Args:
            value: AI动作值
        """
        return self.send_command(AIActionCommand(value))

    # ========== 停止运动 ==========

    def stop_movement(self) -> bool:
        """停止所有轴运动（发送全部轴值为 0）"""
        return all([
            self.send_command(RollCommand(0)),
            self.send_command(PitchCommand(0)),
            self.send_command(HeightCommand(0)),
            self.send_command(YawCommand(0)),
        ])

    # ========== 数据保存 ==========

    def save_data(self) -> bool:
        """保存数据"""
        return self.send_command(SaveDataCommand())

    # ========== 数据获取 ==========

    @property
    def robot_state(self) -> Optional[RobotState]:
        """获取最新的机器人状态"""
        return self._robot_state

    @property
    def joint_angles(self) -> Optional[JointAngles]:
        """获取最新的关节角度"""
        return self._joint_angles

    @property
    def joint_velocities(self) -> Optional[JointVelocities]:
        """获取最新的关节角速度"""
        return self._joint_velocities

    # ========== 回调设置 ==========

    def set_robot_state_callback(self, callback: Optional[Callable[[RobotState], None]]):
        """设置机器人状态回调函数"""
        self._robot_state_callback = callback

    def set_joint_angles_callback(self, callback: Optional[Callable[[JointAngles], None]]):
        """设置关节角度回调函数"""
        self._joint_angles_callback = callback

    def set_joint_velocities_callback(self, callback: Optional[Callable[[JointVelocities], None]]):
        """设置关节角速度回调函数"""
        self._joint_velocities_callback = callback

    def set_speaker_state_callback(self, callback: Optional[Callable[[int], None]]):
        """设置扬声器状态回调函数（0=关闭, 1=开启）"""
        self._speaker_state_callback = callback

    # ========== 上下文管理器 ==========

    def __enter__(self):
        self.connect(verify=self._verify)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.disconnect()