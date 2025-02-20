import time
from yasmin import State      # type: ignore
from yasmin import Blackboard # type: ignore
from rclpy.node import Node   # type: ignore
import rclpy                  # type: ignore
from competition_pkg.gestures import Gesture

NAVIGATION_TIMEOUT = 300.0  # seconds before giving up.


PATHS = {
	Gesture.THUMB_UP: [(2, 0.75)],
	Gesture.TWO_FINGER: [(0.5, 1.0)]
}


class GuidingState(State):

	def __init__(self, node: Node, controller: Node) -> None:
		super().__init__(outcomes=["goto_do_nothing"])
		self.node = node
		self.controller = controller

	def execute(self, blackboard: Blackboard) -> str:
		self.node.get_logger().info(f"Executing state {self.__class__.__name__}")
		# get the path
		self.controller.path = list(PATHS.get(blackboard["gesture"], []))
		self.controller.run = True
		self.controller.next_node()

		deadline = time.time() + NAVIGATION_TIMEOUT
		while self.controller.run and rclpy.ok():
			if time.time() > deadline:
				self.controller.run = False
				self.node.get_logger().warn(
					"Navigation timed out : robot may not be available. "
					"Returning to gesture wait."
				)
				break
			time.sleep(0.1)

		self.node.get_logger().info("Guidance finished. Transitioning to gesture.")
		return "goto_do_nothing"
