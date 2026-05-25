import cv2
import rclpy
from rclpy.node import Node
from cv_bridge import CvBridge, CvBridgeError
from sensor_msgs.msg import Image
from .gestures import GestureRecognizer
from pathlib import Path


MODEL_PATH = Path("src/7_lectures/competition_pkg/models/gesture_recognizer.task")


class ImageRecognition(Node):
    def __init__(self):
        super().__init__("image_recognition")
        self.bridge = CvBridge()
        self.gesture_recognizer = GestureRecognizer.load_from_path(MODEL_PATH)
        self.image_sub = self.create_subscription(
            msg_type=Image,
            topic="image",
            callback=self.callback,
            qos_profile=10
        )

    def callback(self, msg: Image):
        try:
            cv_image = self.bridge.imgmsg_to_cv2(img_msg=msg, desired_encoding="bgr8")
        except CvBridgeError as e:
            self.get_logger().error(f"CvBridgeError: {e}")
            return
        # perform the image processing
        (rows, cols, channels) = cv_image.shape
        gesture = self.gesture_recognizer.process_frame(cv_image)
        print(gesture)



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
