from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription(
        [
            Node(
                package="competition_pkg",
                executable="statemachine",
                name="statemachine",
                output="screen"
            ),
            Node(
                package="competition_pkg",
                executable="gesture_recognition",
                name="gesture_recognition",
                output="screen",
                parameters=[
                    {"model_path": "src/7_lectures/competition_pkg/models/gesture_recognizer.task"}
                ]
            )
        ]
    )


if __name__ == "__main__":
    generate_launch_description()
