#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from std_msgs.msg import String
import time

class MockRobotNode(Node):
    def __init__(self):
        super().__init__('mock_robot_node')
        # Subscribe to the exact same topic the LINE bot publishes to
        self.subscription = self.create_subscription(
            String,
            '/hospital_guide/target_room',
            self.listener_callback,
            10)
        self.get_logger().info("STATE: IDLE - Waiting for instructions...")
        self.is_driving = False

    def listener_callback(self, msg):
        target_room = msg.data
        
        # Prevent receiving new commands if already driving
        if self.is_driving:
            self.get_logger().warn(f"Ignored '{target_room}' - Currently driving!")
            return

        self.is_driving = True
        self.get_logger().info(f"STATE: GUIDING - Received command to go to '{target_room}'!")
        self.get_logger().info("Connecting to move_base... driving...")
        
        # Simulate the time it takes to drive down a hallway
        time.sleep(4) 
        
        self.get_logger().info(f"Arrived at {target_room}! Waiting for patient...")
        time.sleep(2)
        
        self.get_logger().info("STATE: RETURNING - Heading back to home base...")
        time.sleep(4)
        
        self.get_logger().info("STATE: IDLE - Back at home. Waiting for next instruction.")
        self.is_driving = False

def main(args=None):
    rclpy.init(args=args)
    mock_robot = MockRobotNode()
    
    try:
        rclpy.spin(mock_robot)
    except KeyboardInterrupt:
        pass
    finally:
        mock_robot.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()