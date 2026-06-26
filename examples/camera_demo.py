"""摄像头使用示例"""
import time
import os
import cv2
from lite3_sdk import CameraClient


def basic_camera_usage():
    """基础摄像头使用 — 保存帧到本地文件"""
    print("=== 基础摄像头使用 ===")

    camera = CameraClient(host="192.168.2.1")

    if not camera.connect():
        print("连接失败")
        return

    # 保存10帧
    os.makedirs("camera_frames", exist_ok=True)

    print("开始采集图像帧...")
    for i in range(10):
        frame = camera.read_frame()
        if frame is not None:
            filename = f"camera_frames/frame_{i+1:03d}.jpg"
            cv2.imwrite(filename, frame)
            print(f"  保存: {filename}")
        else:
            print(f"  读取第{i+1}帧失败")
        time.sleep(0.1)

    print(f"\n共保存 10 帧到 camera_frames/ 目录，可在 Windows 资源管理器中查看")
    camera.disconnect()


def camera_with_callback():
    """使用回调函数处理视频帧"""
    print("=== 使用回调函数处理视频帧 ===")

    os.makedirs("camera_frames", exist_ok=True)

    frame_count = [0]  # 用列表避免闭包问题

    def process_frame(frame):
        frame_count[0] += 1
        cv2.putText(frame, f'Frame: {frame_count[0]}', (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        filename = f"camera_frames/callback_{frame_count[0]:03d}.jpg"
        cv2.imwrite(filename, frame)

    with CameraClient(host="192.168.2.1") as camera:
        camera.set_frame_callback(process_frame)
        camera.start_receiving()

        print("采集 5 秒...")
        time.sleep(5)

    print(f"\n共保存 {frame_count[0]} 帧到 camera_frames/ 目录")


def camera_with_robot():
    """同时使用摄像头和机器人控制"""
    print("=== 摄像头 + 机器人控制 ===")

    from lite3_sdk import Lite3Client

    os.makedirs("camera_frames", exist_ok=True)

    camera = CameraClient(host="192.168.2.1")
    robot = Lite3Client(host="192.168.1.120")

    if not camera.connect() or not robot.connect(verify=False):
        print("连接失败")
        return

    robot.start_heartbeat()

    frame_idx = [0]

    def save_frame(frame):
        frame_idx[0] += 1
        cv2.putText(frame, f'Frame: {frame_idx[0]}', (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        cv2.imwrite(f"camera_frames/robot_{frame_idx[0]:03d}.jpg", frame)

    camera.set_frame_callback(save_frame)
    camera.start_receiving()

    print("起立...")
    robot.stand_toggle()
    time.sleep(3)

    print("移动模式...")
    robot.set_moving_mode()
    time.sleep(1)

    print("前进...")
    for _ in range(50):
        robot.set_pitch(10000)
        time.sleep(0.1)

    print("停止...")
    robot.stop_movement()

    camera.disconnect()
    robot.disconnect()
    print(f"\n共保存 {frame_idx[0]} 帧到 camera_frames/ 目录")


if __name__ == "__main__":
    print("选择示例:")
    print("1. 基础摄像头使用")
    print("2. 使用回调函数")
    print("3. 摄像头 + 机器人控制")

    choice = input("请输入选择 (1/2/3): ").strip()

    if choice == "1":
        basic_camera_usage()
    elif choice == "2":
        camera_with_callback()
    elif choice == "3":
        camera_with_robot()
    else:
        print("无效选择")
