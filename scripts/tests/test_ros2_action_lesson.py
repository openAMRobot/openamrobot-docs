"""Guard the documented ROS 2 Jazzy Fibonacci action package commands."""
from pathlib import Path
import unittest

LESSON = (
    Path(__file__).resolve().parents[2]
    / "docs"
    / "foundations"
    / "ros2"
    / "services-and-actions.md"
)


class Ros2ActionLessonTests(unittest.TestCase):
    def test_action_tutorial_package_is_installed_and_used(self):
        text = LESSON.read_text(encoding="utf-8")
        self.assertIn("ros-jazzy-action-tutorials-cpp", text)
        self.assertIn(
            "ros2 run action_tutorials_cpp fibonacci_action_server", text
        )
        self.assertIn(
            "ros2 run action_tutorials_cpp fibonacci_action_client", text
        )

    def test_action_examples_do_not_use_demo_nodes_cpp(self):
        text = LESSON.read_text(encoding="utf-8")
        self.assertNotIn(
            "ros2 run demo_nodes_cpp fibonacci_action_server", text
        )
        self.assertNotIn(
            "ros2 run demo_nodes_cpp fibonacci_action_client", text
        )


if __name__ == "__main__":
    unittest.main()
