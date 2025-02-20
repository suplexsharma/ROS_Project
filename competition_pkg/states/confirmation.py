import rclpy
from rclpy.duration import Duration
from rclpy.node import Node
from yasmin import State
from yasmin import Blackboard
import time


class ConfirmationState(State):
    """Confirms the desired destination"""

    def __init__(self, node: Node):
        super().__init__(outcomes=["goto_guiding"])
        self.node = node

    def execute(self, blackboard: Blackboard) -> str:
        gesture = blackboard["gesture"]
        if gesture is None:
            raise RuntimeError("Impossible state: no gesture has been received yet.")
        self.node.get_logger().info(f"Recognized gesture: {gesture}.")
        time.sleep(3)
        return "goto_guiding"