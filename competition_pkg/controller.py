#!/usr/bin/env python3
# -*-encoding:UTF-8-*-

# Import ROS2 related modules
import math
import rclpy                           # type: ignore
from rclpy.node import Node            # type: ignore
from geometry_msgs.msg import Twist    # type: ignore
from sensor_msgs.msg import LaserScan  # type: ignore
from tf2_ros import TransformException # type: ignore



# Controller constants.
MAX_LINEAR_VEL:float = 0.2    # (m/s) Maximum velocity in a straight line.
MAX_ANGULAR_VEL:float = 1.0   # (rad/s) Maximum angular velocity.
ACCEPTANCE_RADIUS:float = 0.2 # (m) Radius at which we consider a point to be reached.
GOAL_TOLERANCE:float = 0.05   # (m) Radius at which we consider the goal to be reached.

# Obstacle detection constants.
ROBOT_HALF_WIDTH = 0.10 # (m) Half of the robot width.
MAX_LOOKAHEAD_DIST = 0.4    # (m) Maximum lookahead range for obstacle detection.



class TurtlebotController(Node):


	def __init__(self) -> None :
		super().__init__("turtlebot_controller")

		# Publisher and timer for the bot control commands.
		self.publisher = self.create_publisher(msg_type=Twist, topic="cmd_vel", qos_profile=10)
		self.timer = self.create_timer(timer_period_sec=0.1, callback=self.timer_callback)

		# Lidar callback for obstacle detection.
		self.scan_sub = self.create_subscription(msg_type=LaserScan, topic="/scan", callback=self.scan_callback, qos_profile=10)
		
		# The trajectory to follow description 
		self.path:tuple[float,float] = []
		self.final:bool = True
		self.target_x:float = 0
		self.target_y:float = 0

		# Guard to start/stop the autopilot as needed.
		self.run:bool = False



	# Callback that is used to gives movement commands to the robot to follow a given trajectory.
	def timer_callback(self) -> None :
		if (not self.run) : return # Guard to stop the controller if its not in use.

		# If there is nothing to do the robot is asked to stop itself.
		if (len(self.path) == 0) :
			self.publisher.publish(Twist())
			return

		# Get the robot position and distance toward the target.
		pos = self.get_position()
		if pos is None: return
		x, y, yaw = pos
		dx = self.target_x - x
		dy = self.target_y - y
		distance = math.hypot(dx, dy)

		# If the goal is reached, the bot is stopped.
		if (self.final) :
			if distance < GOAL_TOLERANCE:
				self.get_logger().info("Reached final goal.")
				self.publisher.publish(Twist())
				self.run = False
				return
			
		# Else if the bot is close enough to the point, set the target to the next trajectory point.
		else:
			if distance < ACCEPTANCE_RADIUS:
				self.get_logger().info(f"Targetting the next point.")
				self.next_node()
				return

		# Prepare the bot command.
		# It uses a proportional controller. 
		target_angle = math.atan2(dy, dx)
		angle_error = target_angle - yaw
		angle_error = math.atan2(math.sin(angle_error), math.cos(angle_error))
		msg = Twist()
		
		# Get the required angular velocity capped by the maximum angular speed. 
		msg.angular.z = max(min(2.0 * angle_error, MAX_ANGULAR_VEL), -MAX_ANGULAR_VEL)
		
		# Get the required linear velocity depending of the angular error and the next point existence.
		if abs(angle_error) < 0.5:
			if self.final:
				msg.linear.x = max(min(0.5 * distance, MAX_LINEAR_VEL), -MAX_LINEAR_VEL)
			else:
				msg.linear.x = MAX_LINEAR_VEL
		else:
			msg.linear.x = 0.0

		self.publisher.publish(msg)



	# Return the bot position as (x,y,yaw) or None if unable to get it.
	def get_position(self) -> tuple[float, float, float] | None:
		try:
			trans = self.tf_buffer.lookup_transform('map', 'base_link', rclpy.time.Time())

			# X and Y position.
			x = trans.transform.translation.x
			y = trans.transform.translation.y

			# Orientation.
			qx = trans.transform.rotation.x
			qy = trans.transform.rotation.y
			qz = trans.transform.rotation.z
			qw = trans.transform.rotation.w
			yaw = math.atan2(2.0 * (qw * qz + qx * qy), 1.0 - 2.0 * (qy * qy + qz * qz))
			return (x,y,yaw)

		except TransformException as ex:
			self.get_logger().warn(f"Failed to get the position.")
			return None



	# Setup this object state to target the next point of the trajectory.
	def next_node(self) -> None:
		if (len(self.path) == 0) :
			self.publisher.publish(Twist())
			self.run = False
			return
		
		# Get the next point.
		next_point:tuple[float,float] = self.path[0]
		self.path.pop(0)

		# Set it as a target.
		self.final:bool = len(self.path) == 0
		self.target_x:float = next_point[0]
		self.target_y:float = next_point[1]



	# Callback for the Lidar obstacle detection.
	def scan_callback(self, msg: LaserScan) -> None:
		if not self.run: return
		obstacle_found = False

		# Calculate how far we should check for an obstacle.
		pos = self.get_position()
		if pos is None: return
		x, y, _ = pos
		dx = self.target_x - x
		dy = self.target_y - y
		distance = math.hypot(dx, dy)
		lookahead_dist = min(MAX_LOOKAHEAD_DIST, distance + ROBOT_HALF_WIDTH)

		# Loop over the Lidar rays.
		for i, r in enumerate(msg.ranges):
			if r < 0.05 or r > 10.0 or math.isinf(r) or math.isnan(r): continue

			# Get the found point coordinates in the robot carthesian coordinates.
			theta = msg.angle_min + i * msg.angle_increment
			x = r * math.cos(theta)
			y = r * math.sin(theta)

			# Ensure that there is not any obstacle.
			if (0.0 < x < lookahead_dist) and (-ROBOT_HALF_WIDTH < y < ROBOT_HALF_WIDTH):
				obstacle_found = True
				break

		if obstacle_found :
			
			# [TODO]: Add a callback to a local pathfinding algorithm to update the trajectory then
			# actualize the current target. For now the robot is stopped.

			self.publisher.publish(Twist())
	
			return 









# Dont think this is useful here but anyway.

def main(args=None):
	rclpy.init(args=args)
	node = TurtlebotController()
	rclpy.spin(node)
	node.destroy_node()
	rclpy.shutdown()

if __name__ == "__main__":
	main()
