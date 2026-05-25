import rclpy
from rclpy.duration import Duration
from rclpy.node import Node
from std_msgs.msg import Int32
from yasmin import State
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
            outcomes=["goto_do_nothing", "goto_wait_gesture"])
        self.node = node

    def received_gesture(self, blackboard: Blackboard, gesture: int):
        gesture = Gesture(gesture.data)
        if gesture == Gesture.NO_GESTURE or gesture == Gesture.THUMB_UP:
            return "goto_wait_gesture"
        return "goto_do_nothing"