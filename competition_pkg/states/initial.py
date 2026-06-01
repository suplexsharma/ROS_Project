import rclpy
from rclpy.duration import Duration
from rclpy.node import Node
from yasmin import State
from yasmin import Blackboard


class InitialState(State):
	"""Initial state"""

	def __init__(self, node: Node):
		# super().__init__(outcomes=["goto_wait_gesture"])
		super().__init__(outcomes=["goto_guide"])
		self.node = node

	def execute(self, blackboard: Blackboard) -> str:

		self.node.get_logger().info("--- TEST ---")
		blackboard["robot_path"] = [(-0.5, -0.5), (-0.5, 0.5), (0.5, 0.5), (-0.5, -0.5)]
		return "goto_guide"


		self.node.get_logger().info(f"Executing state {self.__class__.__name__}")
		return "goto_wait_gesture"
