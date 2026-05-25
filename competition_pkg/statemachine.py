import rclpy
from rclpy.node import Node
from yasmin import StateMachine
from yasmin_viewer import YasminViewerPub

from .states import InitialState, WaitingForGestureState, DoNothingState


class StateMachineNode(Node):
    def __init__(self):
        super().__init__("state_machine")

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
                "goto_do_nothing": "DO_NOTHING_STATE",
                "goto_wait_gesture": "WAITING_FOR_GESTURE_STATE",
            }
        )

        sm.add_state(
            name="DO_NOTHING_STATE",
            state=DoNothingState(node=self),
            transitions={
                "goto_do_nothing": "DO_NOTHING_STATE",
                "goto_wait_gesture": "WAITING_FOR_GESTURE_STATE"
            }
        )

        # Publish state machine information to Yasmin Viewer
        YasminViewerPub(fsm_name="STATE_MACHINE", fsm=sm)
        # Execute the state machine
        outcome = sm()
        # Display log
        self.get_logger().info("State Machine finished with outcome: " + outcome)


def main(args=None):
    # Initialize the ROS2 Python client library
    rclpy.init(args=args)

    # Create an instance of the StateMachineNode class
    node = StateMachineNode()

    # Cleanup
    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
