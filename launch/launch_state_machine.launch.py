from launch.actions import DeclareLaunchArgument
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration
from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    pc_only = DeclareLaunchArgument(
        "pconly",
        default_value="true",
        description="Use the PC only (for debugging purposes)"
    )

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
            ),
            Node(
                package="yasmin_viewer",
                executable="yasmin_viewer_node",
                name="yasmin_viewer"
            ),
            Node(
                package="image_tools",
                executable="cam2image",
                name="cam2image",
                condition=IfCondition(LaunchConfiguration("pconly"))
            )
        ]
    )


if __name__ == "__main__":
    generate_launch_description()
