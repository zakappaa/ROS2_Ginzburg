import math
import random
from collections import deque

import rclpy
from rclpy.node import Node
from std_msgs.msg import Bool, Float32


class SensorNode(Node):

    def __init__(self):
        super().__init__('sensor_node')
        self.declare_parameter('publish_rate', 10.0)
        self.declare_parameter('window_size', 5)
        self.declare_parameter('threshold', 0.5)  
        self.declare_parameter('noise_std', 0.05)     
        self.declare_parameter('spike_probability', 0.03) 
        self.declare_parameter('period', 20.0) 

        self.rate = self.get_parameter('publish_rate').value
        self.window = deque(maxlen=self.get_parameter('window_size').value)
        self.noise_std = self.get_parameter('noise_std').value
        self.spike_probability = self.get_parameter('spike_probability').value
        self.period = self.get_parameter('period').value

        self.raw_pub = self.create_publisher(Float32, '/sensor_data', 10)
        self.filtered_pub = self.create_publisher(Float32, '/sensor_data_filtered', 10)
        self.alarm_pub = self.create_publisher(Bool, '/sensor_alarm', 10)

        self.step = 0
        self.alarm = False
        self.timer = self.create_timer(1.0 / self.rate, self.timer_callback)

        self.get_logger().info(
            f'Sensor Node started: rate={self.rate} Hz, '
            f'window={self.window.maxlen}, threshold={self.get_parameter("threshold").value} m')

    def read_sensor(self):
        t = self.step / self.rate
        value = 1.25 + 0.9 * math.sin(2.0 * math.pi * t / self.period)
        value += random.gauss(0.0, self.noise_std)
        if random.random() < self.spike_probability:
            value = random.uniform(0.05, 0.15)
        return max(value, 0.02)

    def timer_callback(self):
        raw = self.read_sensor()
        self.step += 1

        self.window.append(raw)
        filtered = sum(self.window) / len(self.window)

        self.raw_pub.publish(Float32(data=raw))
        self.filtered_pub.publish(Float32(data=filtered))
        threshold = self.get_parameter('threshold').value
        critical = filtered < threshold
        if critical:
            self.get_logger().warn(
                f'CRITICAL: filtered={filtered:.2f} m is below threshold {threshold:.2f} m',
                throttle_duration_sec=1.0)
        elif self.alarm:
            self.get_logger().info(f'Value back to normal: filtered={filtered:.2f} m')
        self.alarm = critical
        self.alarm_pub.publish(Bool(data=self.alarm))

        self.get_logger().info(
            f'raw={raw:.2f} m, filtered={filtered:.2f} m', throttle_duration_sec=1.0)


def main(args=None):
    rclpy.init(args=args)
    node = SensorNode()
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
