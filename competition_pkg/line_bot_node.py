#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import threading

# 1. Initialize the Flask web server
app = Flask(__name__)

# 2. Add your LINE credentials here
LINE_CHANNEL_ACCESS_TOKEN = 'RI8AK2i2Z96AI4+sUCmvmRcaU0/hJmA8zP7FN9G5TZ8YSgzclIWfYlG5f51aJgpE9L5TcvUNNBsAd+4uEolDlPYm0zNORJulH1iZOj7l8NdRKcqeR3LMGdE3yX9wedb0Y9VOEp573eJ4b758vNafTAdB04t89/1O/w1cDnyilFU='
LINE_CHANNEL_SECRET = '5e67637264614bed3d8b958da2f89c52'

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# Global variable to hold our ROS 2 Publisher
ros_node = None

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_text = event.message.text.lower()
    
    valid_rooms = ["pharmacy", "mri room", "reception"]
    
    if user_text in valid_rooms:
        # Publish the command to the ROS network!
        msg = String()
        msg.data = user_text
        ros_node.publisher_.publish(msg)
        
        ros_node.get_logger().info(f"Published to ROS: {user_text}")
        reply_msg = f"Command accepted. Navigating to {user_text}."
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply_msg))
    else:
        reply_msg = "Unknown room. Please type 'pharmacy', 'mri room', or 'reception'."
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply_msg))

class LineBridgeNode(Node):
    def __init__(self):
        super().__init__('line_bridge_node')
        # Create the publisher that our State Machine will listen to
        self.publisher_ = self.create_publisher(String, '/hospital_guide/target_room', 10)
        self.get_logger().info("LINE Bridge Node is online and waiting for messages.")

def run_flask():
    # Run the web server on port 5000
    app.run(host='0.0.0.0', port=5000, use_reloader=False)

def main(args=None):
    global ros_node
    rclpy.init(args=args)
    
    ros_node = LineBridgeNode()
    
    # Start the Flask web server in the background
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.start()
    
    # Keep the ROS 2 node running
    try:
        rclpy.spin(ros_node)
    except KeyboardInterrupt:
        pass
    finally:
        ros_node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()