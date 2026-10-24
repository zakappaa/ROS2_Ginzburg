import math

import cv2
import numpy as np
import rclpy
from rclpy.node import Node
from cv_bridge import CvBridge
from sensor_msgs.msg import Image


class CameraSimNode(Node):

    def __init__(self):
        super().__init__('camera_sim_node')
        self.declare_parameter('fps', 15.0) 
        self.declare_parameter('noise', 4.0)
        self.declare_parameter('topic', '/camera/image')
        self.fps = self.get_parameter('fps').value
        self.noise = self.get_parameter('noise').value
        topic = self.get_parameter('topic').value

        self.width, self.height = 640, 480
        self.bridge = CvBridge()
        self.publisher_ = self.create_publisher(Image, topic, 10)
        self.background = self.make_background()
        self.frame_id = 0
        self.timer = self.create_timer(1.0 / self.fps, self.tick)
        self.get_logger().info(
            f'Camera simulator started: {self.width}x{self.height}, {self.fps} fps, topic {topic}')

    def make_background(self):
        gradient = np.linspace(40, 120, self.height, dtype=np.uint8)
        gray = np.repeat(gradient[:, None], self.width, axis=1)
        frame = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
        cv2.rectangle(frame, (60, 300), (220, 420), (230, 230, 230), -1)
        cv2.circle(frame, (500, 120), 50, (60, 200, 60), -1)
        triangle = np.array([[330, 420], [420, 280], [510, 420]])
        cv2.fillPoly(frame, [triangle], (0, 220, 220))
        cv2.putText(frame, 'SIM CAMERA', (20, 465),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 2)
        return frame

    def tick(self):
        frame = self.background.copy()
        t = self.frame_id / self.fps
        x = int(self.width / 2 + 220 * math.sin(0.8 * t))
        y = int(self.height / 2 + 120 * math.sin(1.3 * t))
        cv2.circle(frame, (x, y), 35, (0, 140, 255), -1)
        if self.noise > 0:
            noisy = frame + np.random.normal(0.0, self.noise, frame.shape)
            frame = np.clip(noisy, 0, 255).astype(np.uint8)

        msg = self.bridge.cv2_to_imgmsg(frame, encoding='bgr8')
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = 'camera'
        self.publisher_.publish(msg)
        self.frame_id += 1


def main(args=None):
    rclpy.init(args=args)
    node = CameraSimNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
