import math
import rclpy                           # type: ignore
from rclpy.node import Node            # type: ignore
from geometry_msgs.msg import Twist    # type: ignore
from sensor_msgs.msg import LaserScan  # type: ignore
from tf2_ros import TransformException # type: ignore
from tf2_ros.buffer import Buffer      # type: ignore
from tf2_ros.transform_listener import TransformListener # type: ignore



# Controller constants.
MAX_LINEAR_VEL:float = 0.1    # (m/s) Maximum velocity in a straight line.
MAX_ANGULAR_VEL:float = 0.5   # (rad/s) Maximum angular velocity.
ACCEPTANCE_RADIUS:float = 0.1 # (m) Radius at which we consider a point to be reached.
GOAL_TOLERANCE:float = 0.05   # (m) Radius at which we consider the goal to be reached.

# Potential Fields constants.
W_ATTRACT:float = 1.0         # Attraction weight toward the target.
W_REPULSE:float = 1.0         # Repulsion weight from obstacles.
SAFE_DIST:float = 0.5         # (m) Distance at which obstacles start repulsing the bot.
MAX_REPULSION:float = 3.0     # Maximum repulsion force allowed.
TANGENT_WEIGHT:float = 0.6    # Tangential force weight to slide along obstacles.



class Controller(Node):

	def __init__(self) -> None:
		super().__init__("turtlebot_controller")

		# Publisher and timer for the bot control commands.
		self.publisher = self.create_publisher(msg_type=Twist, topic="cmd_vel", qos_profile=10)
		self.timer = self.create_timer(timer_period_sec=0.1, callback=self.timer_callback)

		# Lidar callback for obstacle detection.
		self.scan_sub = self.create_subscription(msg_type=LaserScan, topic="/scan", callback=self.scan_callback, qos_profile=10)
		
		# TF2 Initialization.
		self.tf_buffer = Buffer()
		self.tf_listener = TransformListener(self.tf_buffer, self)

		# The trajectory to follow description. 
		self.path:list[tuple[float,float]] = []
		self.final:bool = True
		self.target_x:float = 0.0
		self.target_y:float = 0.0

		# Local repulsion force vector.
		self.repulse_x:float = 0.0
		self.repulse_y:float = 0.0

		# Guard to start/stop the autopilot as needed.
		self.run:bool = False

		# Consecutive TF failures — stops navigation if robot is unavailable.
		self._tf_failures:int = 0
		self._TF_FAILURE_LIMIT:int = 20  # ~2 seconds at 10 Hz



	# Return the bot position as (x,y,yaw) or None if unable to get it.
	def get_position(self) -> tuple[float, float, float] | None:
		try:
			trans = self.tf_buffer.lookup_transform('odom', 'base_link', rclpy.time.Time())
			# trans = self.tf_buffer.lookup_transform('map', 'base_link', rclpy.time.Time())
			x = trans.transform.translation.x
			y = trans.transform.translation.y
			qx = trans.transform.rotation.x
			qy = trans.transform.rotation.y
			qz = trans.transform.rotation.z
			qw = trans.transform.rotation.w
			yaw = math.atan2(2.0 * (qw * qz + qx * qy), 1.0 - 2.0 * (qy * qy + qz * qz))
			return (x, y, yaw)
		except TransformException as ex:
			self.get_logger().warn("Failed to get the position.")
			return None


	# Setup this object state to target the next point of the trajectory.
	def next_node(self) -> None:
		if len(self.path) == 0:
			self.publisher.publish(Twist())
			self.run = False
			return
		next_point:tuple[float,float] = self.path[0]
		self.path.pop(0)
		self.final:bool = len(self.path) == 0
		self.target_x:float = next_point[0]
		self.target_y:float = next_point[1]



	def timer_callback(self) -> None:
		if not self.run: return

		pos = self.get_position()
		if pos is None:
			self._tf_failures += 1
			if self._tf_failures >= self._TF_FAILURE_LIMIT:
				self.get_logger().warn("Robot TF unavailable — running without a robot? Stopping autopilot.")
				self.run = False
				self._tf_failures = 0
			return
		
		self._tf_failures = 0
		x, y, yaw = pos
		dx = self.target_x - x
		dy = self.target_y - y
		distance = math.hypot(dx, dy)

		if self.final:
			if distance < GOAL_TOLERANCE:
				self.get_logger().info("Reached final goal.")
				self.publisher.publish(Twist())
				self.run = False
				return
		else:
			if distance < ACCEPTANCE_RADIUS:
				self.get_logger().info("Targeting the next point.")
				self.next_node()
				return
		
		target_angle_global = math.atan2(dy, dx)
		angle_error = target_angle_global - yaw
		angle_error = math.atan2(math.sin(angle_error), math.cos(angle_error))
		
		attr_x = math.cos(angle_error)
		attr_y = math.sin(angle_error)

		final_x = (attr_x * W_ATTRACT) + (self.repulse_x * W_REPULSE)
		final_y = (attr_y * W_ATTRACT) + (self.repulse_y * W_REPULSE)
		final_angle = math.atan2(final_y, final_x)
		
		msg = Twist()
		msg.angular.z = max(min(2.0 * final_angle, MAX_ANGULAR_VEL), -MAX_ANGULAR_VEL)
		
		speed_factor = max(0.0, math.cos(final_angle))
		
		if self.final:
			target_speed = max(min(0.5 * distance, MAX_LINEAR_VEL), -MAX_LINEAR_VEL)
		else:
			target_speed = MAX_LINEAR_VEL
			
		msg.linear.x = target_speed * speed_factor
		self.publisher.publish(msg)



	def scan_callback(self, msg: LaserScan) -> None:
		if not self.run: return
		
		rep_x = 0.0
		rep_y = 0.0
		hit_count = 0

		for i, r in enumerate(msg.ranges):
			if r < 0.05 or r > 10.0 or math.isinf(r) or math.isnan(r): continue
			if r < SAFE_DIST:
				safe_r = max(r, 0.15)
				force = (SAFE_DIST - safe_r) / (safe_r * safe_r)
				
				theta = msg.angle_min + i * msg.angle_increment
				
				rx = -force * math.cos(theta)
				ry = -force * math.sin(theta)
				
				tx = ry * TANGENT_WEIGHT
				ty = -rx * TANGENT_WEIGHT
				
				rep_x += rx + tx
				rep_y += ry + ty
				hit_count += 1

		if hit_count > 0:
			rep_x /= hit_count
			rep_y /= hit_count

		current_rep_mag = math.hypot(rep_x, rep_y)
		if current_rep_mag > MAX_REPULSION:
			scale = MAX_REPULSION / current_rep_mag
			rep_x *= scale
			rep_y *= scale

		self.repulse_x = rep_x
		self.repulse_y = rep_y
