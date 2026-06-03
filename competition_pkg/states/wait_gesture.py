import time
import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from std_msgs.msg import Int32
from yasmin_ros.monitor_state import MonitorState
from yasmin import Blackboard
from competition_pkg.gestures import Gesture


class WaitingForGestureState(MonitorState):
    """Waiting for gesture state.
    The robot waits for the user to do any gesture.
    """

    def __init__(self, node: Node):
        super().__init__(
            topic_name="gesture",
            msg_type=Int32,
            monitor_handler=self.received_gesture,
            outcomes=["goto_confirm_gesture", "goto_wait_gesture"])
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

    def received_gesture(self, blackboard: Blackboard, gesture: int):
        gesture = Gesture(gesture.data)
        if gesture == Gesture.NO_GESTURE or gesture == Gesture.THUMB_UP:
            return "goto_wait_gesture"
        blackboard["gesture"] = gesture
        blackboard["robot_path"] = [] # TODO: put the right path for the robot here
        return "goto_confirm_gesture"
