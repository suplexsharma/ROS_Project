# ROS Project — Gesture-Controlled Robot Navigation

A ROS 2 package that lets you guide a TurtleBot using hand gestures (or a keyboard fallback). It combines a MediaPipe gesture recogniser, a YASMIN finite state machine, and a Potential-Fields motion controller with LiDAR-based obstacle avoidance.

---

## Features

- **Real-time gesture recognition** via webcam using MediaPipe
- **Keyboard fallback** when no webcam or model is available
- **Finite state machine** (YASMIN) managing robot behaviour across states
- **Potential-Fields navigation** with smooth obstacle avoidance using LiDAR
- **YASMIN Viewer** integration for live state machine visualisation

---

## Package Structure

```
competition_pkg/
├── controller/
│   ├── controller.py       # Potential-Fields navigation controller
│   └── controller2.py      # Alternative controller
├── states/
│   ├── initial.py          # InitialState
│   ├── wait_gesture.py     # WaitingForGestureState
│   ├── guiding.py          # GuidingState (drives the robot)
│   └── do_nothing.py       # DoNothingState
├── gesture_node.py         # Gesture recognition node (camera + keyboard)
└── statemachine.py         # Main state machine node entry point
launch/
└── launch_state_machine.launch.py
gesture_recognizer.task     # MediaPipe gesture model
requirements.txt
```

---

## State Machine

```
INITIAL_STATE
     |
     └──► GUIDING_STATE ──► WAITING_FOR_GESTURE_STATE
                ▲                      |
                └──────────────────────┘
```

| State | Description |
|---|---|
| `INITIAL_STATE` | Sets up and transitions immediately to guiding |
| `GUIDING_STATE` | Drives the robot along a path using the controller |
| `WAITING_FOR_GESTURE_STATE` | Waits for a hand gesture to determine the next action |
| `DO_NOTHING_STATE` | Idles the robot |

---

## Gesture Controls

| Gesture | Key | Action |
|---|---|---|
| Thumb Up | `w` | Move forward |
| Thumb Down | `s` | Move backward |
| Pointing Up | `a` | Turn left |
| Closed Fist | `d` | Turn right |
| Victory | `v` | Go to safe location |
| Open Palm | `p` | Idle / stop |

---

## Prerequisites

- ROS 2 (tested with Humble / Iron)
- Python 3.10+
- [`yasmin`](https://github.com/uleroboticsgroup/yasmin) and `yasmin_viewer`
- `tf2_ros`, `nav_msgs`, `sensor_msgs`, `geometry_msgs`

Install Python dependencies:

```bash
pip install -r requirements.txt
```

---

## Build

```bash
cd ~/ros2_lecture_ws
colcon build --packages-select competition_pkg
source install/setup.bash
```

---

## Run

Launch both the gesture node and the state machine together:

```bash
ros2 launch competition_pkg launch_state_machine.launch.py
```

Or run nodes individually:

```bash
ros2 run competition_pkg gesture_node
ros2 run competition_pkg statemachine
```

---

## Topics

| Topic | Type | Description |
|---|---|---|
| `/gesture` | `std_msgs/String` | Published gesture name |
| `/cmd_vel` | `geometry_msgs/Twist` | Robot velocity commands |
| `/scan` | `sensor_msgs/LaserScan` | LiDAR input for obstacle avoidance |

---

## Navigation Controller

The controller uses a **Potential-Fields** algorithm:

- **Attraction** force pulls the robot toward the current waypoint
- **Repulsion** force pushes away from obstacles detected via LiDAR
- **Tangential** component helps the robot slide around obstacles rather than getting stuck
- Velocity is clamped to `0.1 m/s` linear and `0.5 rad/s` angular

---

## Author

**Suraj Paliwal** — [surajpaliwal.developer@gmail.com](mailto:surajpaliwal.developer@gmail.com)
