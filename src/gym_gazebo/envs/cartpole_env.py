# Custom gymnasium environment for cartpole training
import rclpy
import time
import math
import numpy as np
import gymnasium as gym
from rclpy.node import Node as RosNode
from gym_gazebo.core.gazebo_env import GazeboEnv
from sensor_msgs.msg import JointState
from std_msgs.msg import Float64MultiArray
from gym_gazebo.utils import cartpole_utils

class CartpoleEnv(GazeboEnv):
    def __init__(self):
        # Intializing ROS2
        rclpy.init(args=None)

        # Passing arguments to parent class
        super(CartpoleEnv, self).__init__('my_agent_bringup',
                                          'my_cartpole.launch.xml',
                                          'cartpole_gym')

        # Setting up ROS2 nodes
        self.ros_node = RosNode('cartpole_RL')

        # Initializing variables
        self.is_resetting = False
        self.latest_obs = None
        self.new_obs_event = False
        self.theta_limit = 12 * math.pi / 180
        self.x_limit = 15

        # Setting the observation and action spaces
        low_bounds = np.array([-self.theta_limit * 2, -15, -np.inf, -np.inf], dtype=np.float32)
        high_bounds = np.array([self.theta_limit * 2, 15, np.inf, np.inf], dtype=np.float32)
        self.observation_space = gym.spaces.Box(low=low_bounds, high=high_bounds, dtype=np.float32)
        self.action_space = gym.spaces.Discrete(2)

        # ROS2 topics
        observation_topic = "/joint_states"
        velocity_topic = "/cart_velocity_controller/commands"

        # Publishing and subscribing to ROS2 topics
        self.pub_cmd_vel_msg = self.ros_node.create_publisher(
            Float64MultiArray, velocity_topic, 10)
            
        self.sub_obs = self.ros_node.create_subscription(
            JointState, observation_topic, self.obs_feed_, 10)
    
    ## OBSERVATION CALLBACK

    def obs_feed_(self, msg: JointState):
        # Takes in observation, returns a flag an observation is recieved
        if not self.is_resetting:
            # INDEX:
                # 0: pole angle (rad)
                # 1: cart position (m)
                # 2: pole angular velocity (rad/s)
                # 3: cart velocity (m/s)  
            self.latest_obs = np.concatenate([msg.position, msg.velocity]).astype(np.float32)
            self.new_obs_event = True
            # print("recieved observation!")

    ## MAIN FUNCTIONS:

    def reset(self, seed=None, options=None):
        self.new_obs_event = False
        self.is_resetting = True
        print("Resetting")

        # Zero out velocities
        vel_cmd = Float64MultiArray()
        vel_cmd.data = [0.0]
        self.pub_cmd_vel_msg.publish(vel_cmd)

        time.sleep(0.02)

        # Pause the sim
        self._pause_sim(True)

        # Reset position and joints
        self._reset_agents()

        # Unpause the sim
        self._pause_sim(False)

        time.sleep(0.1) # Wait 100 ms
        
        self.is_resetting = False

        # Wait for next observation to come in before kickstarting the data loop
        while not self.new_obs_event:
            # Telling executor (node) to spin
            rclpy.spin_once(self.ros_node, timeout_sec=0.01)
        self.new_obs_event = True

        print("Done resetting")
        return self.latest_obs, {}

    def step(self, action: int):
        # Process the action
        velocity = cartpole_utils.process_action(action, self.latest_obs[3])

        # Creating the velocity command
        vel_cmd = Float64MultiArray()
        vel_cmd.data = [velocity]

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

        reward, terminated = cartpole_utils.process_obs(self.latest_obs, self.x_limit, self.theta_limit)

        return self.latest_obs, reward, terminated, truncated, {}


    ### HELPER FUNCTIONS:

    # Shutting down ROS2
    def user_close(self):
        self.ros_node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()