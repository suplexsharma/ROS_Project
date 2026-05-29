import rclpy
from rclpy.duration import Duration
from rclpy.node import Node
from yasmin import State
from yasmin import Blackboard


class ConfirmationState(State):
    """Confirms the desired destination"""

    def __init__(self, node: Node):
        super().__init__(outcomes=["goto_do_nothing", "goto_wait_gesture"])
        self.node = node

    def execute(self, blackboard: Blackboard) -> str:
        gesture = blackboard["gesture"]
        if gesture is None:
            raise RuntimeError("Impossible state: no gesture has been received yet.")
        confirm = "y" # TODO: make it from user input
        # confirm = input(f"Received gesture {gesture}, do you confirm it? (y/n): ")
        if confirm == "y":
            return "goto_do_nothing"
        return "goto_wait_gesture"
