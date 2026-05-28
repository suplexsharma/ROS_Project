import threading
import rclpy
from rclpy.node import Node
from yasmin import StateMachine
from yasmin_viewer import YasminViewerPub
from rclpy.executors import MultiThreadedExecutor

from .states import InitialState, WaitingForGestureState, DoNothingState, GuidingState
from controller import Controller


class StateMachineNode(Node):
	def __init__(self, controller: Node):
		super().__init__("state_machine")
		self.controller = controller

		# create an instance of the StateMachine class
		sm = StateMachine(outcomes=["EXIT"])

		# add the states to the state machine
		sm.add_state(
			name="INITIAL_STATE",
			state=InitialState(node=self),
			transitions={
				"goto_wait_gesture": "WAITING_FOR_GESTURE_STATE",
			}
		)

		sm.add_state(
			name="WAITING_FOR_GESTURE_STATE",
			state=WaitingForGestureState(node=self),
			transitions={
				"goto_do_nothing": "DO_NOTHING_STATE"
			}
		)

		sm.add_state(
			name="DO_NOTHING_STATE",
			state=DoNothingState(node=self),
			transitions={
				"goto_do_nothing": "DO_NOTHING_STATE"
			}
		)

		sm.add_state(
			name="GUIDING_STATE",
			state=GuidingState(node=self, controller=self.controller),
			transitions={
				"goto_gesture": "WAITING_FOR_GESTURE_STATE"
			}
		)

		# Publish state machine information to Yasmin Viewer
		YasminViewerPub(fsm_name="STATE_MACHINE", fsm=sm)
		self.sm_thread = threading.Thread(target=self.run_sm)
		self.sm_thread.start()

	def run_sm(self):
		outcome = self.sm()
		self.get_logger().info("State Machine finished with outcome: " + outcome)


def main(args=None):
	rclpy.init(args=args)

	controller_node = Controller()
	sm_node = StateMachineNode(controller=controller_node)
	executor = MultiThreadedExecutor()
	executor.add_node(controller_node)
	executor.add_node(sm_node)

	try:
		executor.spin()
	except KeyboardInterrupt:
		pass
	finally:
		executor.shutdown()
		controller_node.destroy_node()
		sm_node.destroy_node()
		rclpy.shutdown()


if __name__ == "__main__":
	main()
