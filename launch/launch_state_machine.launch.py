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
            )
        ]
    )


if __name__ == "__main__":
    generate_launch_description()
