import rclpy                                # type: ignore
from rclpy.node import Node                 # type: ignore
from rclpy.action import ActionClient       # type: ignore
from nav2_msgs.action import NavigateToPose # type: ignore

class Controller(Node):
	def __init__(self) -> None:
		super().__init__("turtlebot_controller")
		self.nav_client = ActionClient(self, NavigateToPose, 'navigate_to_pose')
		
		self.path: list[tuple[float,float]] = []
		self.run: bool = False

	def next_node(self) -> None:
		if len(self.path) == 0:
			self.run = False
			return
			
		next_point = self.path.pop(0)
		self.get_logger().info(f"Nav2: Envoi vers x={next_point[0]}, y={next_point[1]}")
		
		goal_msg = NavigateToPose.Goal()
		goal_msg.pose.header.frame_id = 'map'
		goal_msg.pose.header.stamp = self.get_clock().now().to_msg()
		
		goal_msg.pose.pose.position.x = next_point[0]
		goal_msg.pose.pose.position.y = next_point[1]
		goal_msg.pose.pose.orientation.w = 1.0
		
		if not self.nav_client.wait_for_server(timeout_sec=5.0):
			self.get_logger().error("Nav2 Server not found..")
			self.run = False
			return
			
		send_goal_future = self.nav_client.send_goal_async(goal_msg)
		send_goal_future.add_done_callback(self.goal_response_callback)

	def goal_response_callback(self, future) -> None:
		goal_handle = future.result()
		if not goal_handle.accepted:
			self.get_logger().error("Trajectory rejected.")
			self.run = False
			return

		self.get_logger().info("Starting guidance to the next point.")
		result_future = goal_handle.get_result_async()
		result_future.add_done_callback(self.get_result_callback)

	def get_result_callback(self, future) -> None:
		self.get_logger().info("Point reached.")
		self.next_node()
