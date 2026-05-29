import threading
import rclpy
from rclpy.node import Node
from yasmin import StateMachine
from yasmin_viewer import YasminViewerPub
from rclpy.executors import MultiThreadedExecutor

from competition_pkg.states import InitialState, WaitingForGestureState, DoNothingState, GuidingState
from competition_pkg.controller import Controller
from competition_pkg.gesture_node import GestureRecognitionNode


class StateMachineNode(Node):
    def __init__(self, controller: Node):
        super().__init__("state_machine")
        self.controller = controller

        sm = StateMachine(outcomes=["EXIT"])

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
                "goto_guiding": "GUIDING_STATE"
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
                "goto_wait_gesture": "WAITING_FOR_GESTURE_STATE"
            }
        )

        YasminViewerPub(fsm_name="STATE_MACHINE", fsm=sm)
        self.sm = sm
        self.sm_thread = threading.Thread(target=self.run_sm)
        self.sm_thread.start()

    def run_sm(self):
        outcome = self.sm()
        self.get_logger().info("State Machine finished with outcome: " + outcome)


def main(args=None):
    rclpy.init(args=args)

    controller_node = Controller()
    gesture_node = GestureRecognitionNode()
    sm_node = StateMachineNode(controller=controller_node)

    executor = MultiThreadedExecutor()
    executor.add_node(controller_node)
    executor.add_node(gesture_node)
    executor.add_node(sm_node)

    try:
        executor.spin()
    except KeyboardInterrupt:
        pass
    finally:
        executor.shutdown()
        controller_node.destroy_node()
        gesture_node.destroy_node()
        sm_node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
