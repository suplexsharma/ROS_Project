import time
import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from yasmin import State
from yasmin import Blackboard


# Adjust these to match your actual map coordinates.
SAFE_LOCATION: tuple[float, float] = (0.0, 0.0)   # home / safe spot on the map

GESTURE_PATHS: dict[str, list[tuple[float, float]]] = {
    "Thumb_Up":    [(1.0,  0.0)],          # move forward
    "Thumb_Down":  [(-1.0, 0.0)],          # move backward
    "Pointing_Up": [(0.0,  1.0)],          # turn left + forward
    "Closed_Fist": [(0.0, -1.0)],          # turn right + forward
    "Victory":     [SAFE_LOCATION],        # two fingers → go to safe location
    "Open_Palm":   [],                     # idle / stop
}


class WaitingForGestureState(State):
    """Waits for a gesture on /gesture, then maps it to a waypoint path."""

    def __init__(self, node: Node):
        super().__init__(outcomes=["goto_guiding"])
        self.node = node
        self._gesture: str | None = None
        self._received: bool = False
        self._sub = node.create_subscription(
            String, "/gesture", self._gesture_cb, 10
        )

    def _gesture_cb(self, msg: String) -> None:
        if not self._received:
            self._gesture = msg.data
            self._received = True

    def execute(self, blackboard: Blackboard) -> str:
        self.node.get_logger().info("Waiting for gesture...")
        self._received = False
        self._gesture = None

        while not self._received and rclpy.ok():
            time.sleep(0.1)

        gesture = self._gesture or ""
        path = GESTURE_PATHS.get(gesture, [])
        blackboard["robot_path"] = path
        self.node.get_logger().info(f"Gesture '{gesture}' → {len(path)} waypoint(s)")
        return "goto_guiding"
