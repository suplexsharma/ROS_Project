import cv2
import rclpy
from rclpy.node import Node
from cv_bridge import CvBridge, CvBridgeError
from sensor_msgs.msg import Image
from std_msgs.msg import String, Int32
from .gestures import GestureRecognizer
from pathlib import Path


class ImageRecognition(Node):
    def __init__(self):
        super().__init__("image_recognition")
        self.bridge = CvBridge()
        self.declare_parameter("model_path", None)
        self.model_path = self.get_parameter("model_path").value
        self.gesture_recognizer = GestureRecognizer.load_from_path(self.model_path)
        self.image_sub = self.create_subscription(
            msg_type=Image,
            topic="image",
            callback=self.callback,
            qos_profile=1
        )
        self.gesture_pub = self.create_publisher(
            msg_type=Int32,
            topic="gesture",
            qos_profile=1
        )

    def callback(self, msg: Image):
        try:
            cv_image = self.bridge.imgmsg_to_cv2(img_msg=msg, desired_encoding="bgr8")
        except CvBridgeError as e:
            self.get_logger().error(f"CvBridgeError: {e}")
            return
        # get the gesture and publish it
        gesture = self.gesture_recognizer.process_frame(cv_image)
        message = Int32()
        message.data = int(gesture)
        self.gesture_pub.publish(message)



def main(args=None):
    """Main function"""
    # Initialize ROS2 Python client library
    rclpy.init(args=args)

    # Create instance of ImageConverter class
    image_recognizer = ImageRecognition()

    try:
        # Run the specified node until it terminates
        rclpy.spin(image_recognizer)
    except KeyboardInterrupt:
        print("Shutting down")

    # Cleanup
    image_recognizer.destroy_node()
    rclpy.shutdown()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
