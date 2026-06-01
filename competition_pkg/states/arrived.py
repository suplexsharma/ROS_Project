import rclpy
from pathlib import Path
from rclpy.duration import Duration
from rclpy.node import Node
from yasmin import State
from yasmin import Blackboard
from sound_play_py.libsoundplay import SoundClient
from rclpy.duration import Duration
import time
import os


class ArrivedState(State):
    """Inform the user that the robot arrived"""

    def __init__(self, node: Node):
        super().__init__(outcomes=["goto_wait_gesture"])
        self.node = node
        self.sound_client = SoundClient(node, blocking=True)
        self.confirm_sound = "src/7_lectures/competition_pkg/sounds/arrived.wav"
        self.confirm_sound = f"{os.getcwd()}/{self.confirm_sound}"

    def execute(self, blackboard: Blackboard) -> str:
        gesture = blackboard["gesture"]
        if gesture is None:
            raise RuntimeError("Impossible state: no gesture has been received yet.")
        if not Path(self.confirm_sound).is_file():
            raise RuntimeError("The file does not exist!")
        self.sound_client.playWave(self.confirm_sound, volume=2.0)
        return "goto_wait_gesture"
