"""摄像头实时显示示例"""
import cv2
from lite3_sdk import CameraClient


def main():
    """连接摄像头并实时显示画面，按 Q 或 ESC 退出"""
    camera = CameraClient(host="192.168.2.1")

    print("正在连接摄像头...")
    if not camera.connect():
        print("连接失败")
        return

    print("已连接，实时显示画面中... (按 Q 或 ESC 退出)")

    try:
        while True:
            frame = camera.read_frame()
            if frame is None:
                continue

            cv2.imshow("Camera", frame)

            key = cv2.waitKey(1) & 0xFF
            if key == ord('q') or key == 27:  # 27 = ESC
                break
    finally:
        cv2.destroyAllWindows()
        camera.disconnect()
        print("已断开连接")


if __name__ == "__main__":
    main()
