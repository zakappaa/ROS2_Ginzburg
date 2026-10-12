import signal
import sys

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from std_msgs.msg import String
from PyQt5.QtCore import QTime, QTimer
from PyQt5.QtWidgets import (
    QApplication, QDoubleSpinBox, QFormLayout, QGridLayout, QLabel,
    QPlainTextEdit, QPushButton, QVBoxLayout, QWidget)


class RobotGuiNode(Node):

    def __init__(self, on_status):
        super().__init__('robot_gui')
        self.publisher_ = self.create_publisher(Twist, '/cmd_vel', 10)
        self.subscription = self.create_subscription(
            String, '/motion_status', lambda msg: on_status(msg.data), 10)

    def send_command(self, linear_x, angular_z):
        msg = Twist()
        msg.linear.x = linear_x
        msg.angular.z = angular_z
        self.publisher_.publish(msg)
        self.get_logger().info(
            f'Published /cmd_vel: linear.x={linear_x:.2f}, angular.z={angular_z:.2f}')


class ControlWindow(QWidget):

    def __init__(self):
        super().__init__()
        self.node = RobotGuiNode(self.show_status)
        self.setWindowTitle('Керування роботом (ROS2)')
        self.setMinimumWidth(420)

        self.linear_speed = self.make_spinbox(0.5)
        self.angular_speed = self.make_spinbox(1.0)
        speeds = QFormLayout()
        speeds.addRow('Лінійна швидкість, м/с:', self.linear_speed)
        speeds.addRow('Кутова швидкість, рад/с:', self.angular_speed)

        buttons = QGridLayout()
        self.add_button(buttons, 'Вперед', 0, 1, 1, 0)
        self.add_button(buttons, 'Ліворуч', 1, 0, 0, 1)
        self.add_button(buttons, 'Стоп', 1, 1, 0, 0)
        self.add_button(buttons, 'Праворуч', 1, 2, 0, -1)
        self.add_button(buttons, 'Назад', 2, 1, -1, 0)

        self.command_label = QLabel('Остання команда: —')
        self.status_box = QPlainTextEdit()
        self.status_box.setReadOnly(True)
        self.status_box.setMaximumBlockCount(200)

        layout = QVBoxLayout(self)
        layout.addLayout(speeds)
        layout.addLayout(buttons)
        layout.addWidget(self.command_label)
        layout.addWidget(QLabel('Статус системи (/motion_status):'))
        layout.addWidget(self.status_box)

        self.ros_timer = QTimer(self)
        self.ros_timer.timeout.connect(
            lambda: rclpy.spin_once(self.node, timeout_sec=0))
        self.ros_timer.start(50)

        self.show_status('GUI запущено, очікування повідомлень /motion_status...')

    def make_spinbox(self, value):
        box = QDoubleSpinBox()
        box.setRange(0.0, 5.0)
        box.setSingleStep(0.1)
        box.setValue(value)
        return box

    def add_button(self, grid, text, row, col, linear_dir, angular_dir):
        button = QPushButton(text)
        button.setMinimumSize(110, 50)
        button.setAutoRepeat(bool(linear_dir or angular_dir))
        button.clicked.connect(
            lambda: self.on_button(text, linear_dir, angular_dir))
        grid.addWidget(button, row, col)

    def on_button(self, text, linear_dir, angular_dir):
        linear_x = linear_dir * self.linear_speed.value()
        angular_z = angular_dir * self.angular_speed.value()
        self.node.send_command(linear_x, angular_z)
        self.command_label.setText(
            f'Остання команда: {text} '
            f'(linear.x={linear_x:.2f}, angular.z={angular_z:.2f})')

    def show_status(self, text):
        time = QTime.currentTime().toString('HH:mm:ss')
        self.status_box.appendPlainText(f'[{time}] {text}')


def main(args=None):
    rclpy.init(args=args)
    app = QApplication(sys.argv)
    window = ControlWindow()
    window.show()
    signal.signal(signal.SIGINT, lambda *_: app.quit())
    app.exec_()

    window.node.send_command(0.0, 0.0)
    window.node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
