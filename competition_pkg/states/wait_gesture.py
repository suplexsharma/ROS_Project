import rclpy
from rclpy.duration import Duration
from rclpy.node import Node
from yasmin import State
from yasmin import Blackboard


class WaitingForGestureState(State):
    """Waiting for gesture state.
    The robot waits for the user to do any gesture.
    """

    def __init__(self, node: Node):
        super().__init__(outcomes=["goto_do_nothing"])
        self.node = node

    def execute(self, blackboard: Blackboard) -> str:
        self.node.get_logger().info(f"Executing state {self.__class__.__name__}")
        return "goto_do_nothing"
