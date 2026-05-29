import sys
import time
import threading
from pathlib import Path

import cv2
import rclpy
from rclpy.node import Node
from std_msgs.msg import String

import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

from ament_index_python.packages import get_package_share_directory


_SRC_MODEL = Path(__file__).resolve().parent.parent / 'gesture_recognizer.task'
_SHARE_MODEL = Path(get_package_share_directory('competition_pkg')) / 'gesture_recognizer.task'
MODEL_PATH = _SRC_MODEL if _SRC_MODEL.exists() else _SHARE_MODEL

CONFIDENCE_THRESHOLD = 0.6

# Keyboard shortcuts for fallback mode (no webcam)
KEYBOARD_MAP = {
    'w': 'Thumb_Up',
    's': 'Thumb_Down',
    'a': 'Pointing_Up',
    'd': 'Closed_Fist',
    'v': 'Victory',
    'p': 'Open_Palm',
}


def setup_recognizer():
    options = vision.GestureRecognizerOptions(
        base_options=python.BaseOptions(model_asset_path=str(MODEL_PATH)),
        running_mode=vision.RunningMode.VIDEO,
        num_hands=2,
        min_hand_detection_confidence=0.4,
        min_hand_presence_confidence=0.4,
        min_tracking_confidence=0.4,
    )
    return vision.GestureRecognizer.create_from_options(options)


def process_frame(frame, recognizer):
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
    result = recognizer.recognize_for_video(mp_image, int(time.time() * 1000))
    if result.gestures and result.hand_landmarks:
        top = result.gestures[0][0]
        return top.category_name, top.score
    return "No Gesture", 0.0


class GestureRecognitionNode(Node):

    def __init__(self) -> None:
        super().__init__("gesture_recognition")
        self._pub = self.create_publisher(String, "/gesture", 10)

        # Try to open the webcam
        self._cap = cv2.VideoCapture(0)
        if self._cap.isOpened() and MODEL_PATH.exists():
            self._start_camera_mode()
        else:
            if not self._cap.isOpened():
                self.get_logger().warn("No webcam found — switching to keyboard fallback.")
            elif not MODEL_PATH.exists():
                self.get_logger().warn(
                    f"Model not found at {MODEL_PATH} — switching to keyboard fallback."
                )
            self._start_keyboard_mode()

    # ------------------------------------------------------------------ camera

    def _start_camera_mode(self) -> None:
        self.get_logger().info(f"Camera mode — model: {MODEL_PATH}")
        self._recognizer = setup_recognizer()
        self._no_gesture_count = 0
        self.create_timer(1.0 / 30.0, self._camera_tick)
        self.get_logger().info("Show a hand gesture to the camera.")

    def _camera_tick(self) -> None:
        ok, frame = self._cap.read()
        if not ok:
            return
        frame = cv2.flip(frame, 1)
        gesture_name, confidence = process_frame(frame, self._recognizer)
        if confidence >= CONFIDENCE_THRESHOLD and gesture_name != "No Gesture":
            self._no_gesture_count = 0
            self._publish(gesture_name)
            self.get_logger().info(f"Gesture: {gesture_name} ({confidence:.2f})")
        else:
            self._no_gesture_count += 1
            if self._no_gesture_count % 90 == 0:
                self.get_logger().info("No gesture detected — show a hand to the camera.")

    # --------------------------------------------------------------- keyboard

    def _start_keyboard_mode(self) -> None:
        self.get_logger().info(
            "\n--- KEYBOARD FALLBACK MODE ---\n"
            "  w → Thumb_Up    (move forward)\n"
            "  s → Thumb_Down  (move backward)\n"
            "  a → Pointing_Up (turn left)\n"
            "  d → Closed_Fist (turn right)\n"
            "  v → Victory     (go to safe location)\n"
            "  p → Open_Palm   (idle / stop)\n"
            "Type a key and press Enter."
        )
        self._kb_thread = threading.Thread(target=self._keyboard_loop, daemon=True)
        self._kb_thread.start()

    def _keyboard_loop(self) -> None:
        while rclpy.ok():
            try:
                key = input().strip().lower()
            except EOFError:
                break
            gesture = KEYBOARD_MAP.get(key)
            if gesture:
                self._publish(gesture)
                self.get_logger().info(f"Keyboard gesture: {gesture}")
            elif key:
                self.get_logger().warn(
                    f"Unknown key '{key}'. Use: w s a d v p"
                )

    # ------------------------------------------------------------------ shared

    def _publish(self, gesture: str) -> None:
        msg = String()
        msg.data = gesture
        self._pub.publish(msg)

    def destroy_node(self) -> None:
        if hasattr(self, '_cap'):
            self._cap.release()
        super().destroy_node()


def main(args=None) -> None:
    rclpy.init(args=args)
    node = GestureRecognitionNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
