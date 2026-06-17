import rclpy
import time
import gymnasium as gym
from gym_gazebo.core.gazebo_env import GazeboEnv
from rclpy.node import Node as RosNode
from gym_gazebo.utils import linefollower_utils
from sensor_msgs.msg import Image as RosImage
from geometry_msgs.msg import Twist as RosTwist

NUM_BINS = 3
NUM_ACTIONS = 3

class LineFollowerEnv(GazeboEnv):
    def __init__(self):
        # Intializing ROS2
        rclpy.init(args=None)

        # Passing arguments to parent class
        super(LineFollowerEnv, self).__init__('my_agent_bringup',
                                            'my_agent.launch.xml',
                                            'monza_gym')

        # Setting up ROS2 node
        self.ros_node = RosNode('line_follower_RL')


        # Initializing variables
        self.is_resetting = False
        self.latest_obs = None
        self.latest_state = None
        self.new_obs_event = False

        # Setting the observation and action spaces
        self.observation_space = gym.spaces.Discrete(NUM_BINS)
        self.action_space = gym.spaces.Discrete(NUM_ACTIONS)

        # ROS2 topics
        observation_topic = "/camera/image_raw"
        velocity_topic = "/cmd_vel"

        # Publishing and subscribing to ROS2 topics
        self.pub_cmd_vel_msg = self.ros_node.create_publisher(
            RosTwist, velocity_topic, 10)
            
        self.sub_obs = self.ros_node.create_subscription(
            RosImage, observation_topic, self.obs_feed_, 10)

    ## OBSERVATION CALLBACK

    def obs_feed_(self, msg: RosImage):
        # Takes in observation, returns a flag an observation is recieved
        if not self.is_resetting:
            self.latest_obs = msg
            self.new_obs_event = True
    
    ## MAIN FUNCTIONS:

    def reset(self, seed=None, options=None):
        self.new_obs_event = False
        self.is_resetting = True
        print("Resetting")

        # Zero out velocities
        vel_cmd = RosTwist()
        vel_cmd.linear.x = 0.0
        vel_cmd.angular.z = 0.0
        self.pub_cmd_vel_msg.publish(vel_cmd)

        # Sleep a bit to ensure the command is sent before pausing the sim
        time.sleep(0.02)

        # Pause the sim
        self._pause_sim(True)

        # Reset position and joints
        self._reset_agents()

        # Unpause the sim
        self._pause_sim(False)

        # Give a bit to settle
        time.sleep(0.1) # Wait 100 ms
        
        self.is_resetting = False

        # Wait for next observation to come in before kickstarting the data loop
        while not self.new_obs_event:
            # Telling executor (node) to spin
            rclpy.spin_once(self.ros_node, timeout_sec=0.01)
        self.new_obs_event = True

        # # Pause the sim after the first observation comes in
        # self._pause_sim(True)
        
        state, _, _ = linefollower_utils.process_obs(self.latest_obs, self.observation_space)
        self.latest_state = state

        print("Done resetting")
        return self.latest_state, {}
    
    def step(self, action: int):
        # Process the action
        vel_cmd = linefollower_utils.process_action(action)

        # Unpause the sim
        self._pause_sim(False)

        # Moving the agent
        self.pub_cmd_vel_msg.publish(vel_cmd)

        # Leave running until next observation comes in
        while not self.new_obs_event:
            rclpy.spin_once(self.ros_node, timeout_sec=0.01)

        # Pause the simulation after the next observation comes in
        self._pause_sim(True)
        # print("Paused sim due to new observation! \n")
        self.new_obs_event = False

        truncated = False

        state, reward, terminated = linefollower_utils.process_obs(self.latest_obs, self.observation_space)
        self.latest_state = state

        return self.latest_state, reward, terminated, truncated, {}
    
    ## HELPER FUNCTIONS

    # Shutting down ROS2
    def user_close(self):
        self.ros_node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()