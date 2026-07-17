import cv2
import rclpy
import time
import gym_gazebo
import gymnasium as gym
import numpy as np
from cv_bridge import CvBridge
from gym_gazebo.core.gazebo_env import GazeboEnv
from rclpy.node import Node as RosNode
from sensor_msgs.msg import Image as RosImage
from geometry_msgs.msg import Twist as RosTwist

NUM_BINS = 3
NUM_ACTIONS = 3

class LineFollowerEnv(GazeboEnv):
    def __init__(self):
        # Intializing ROS2
        rclpy.init(args=None)
        
        super(LineFollowerEnv, self).__init__(launch_pkg='linefollow_ros',
                                    launch_file='my_agent.launch.xml',
                                    world_name='monza_gym')

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
        self._pause_sim(True)
        
        state, _, _ = self.process_obs(self.latest_obs, self.observation_space)
        self.latest_state = state

        print("Done resetting")
        return self.latest_state, {}
    
    
    def step(self, action: int):
        # Process the action
        vel_cmd = self.process_action(action)

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

        state, reward, terminated = self.process_obs(self.latest_obs, self.observation_space)
        self.latest_state = state

        return self.latest_state, reward, terminated, truncated, {}
    
    ## HELPER FUNCTIONS

    def process_action(self, action: int):
        vel_cmd = RosTwist()

        if action == 0: # Left
            vel_cmd.linear.x = 1.0
            vel_cmd.angular.z = 1.5
        elif action == 1: # Forward
            vel_cmd.linear.x = 1.0
            vel_cmd.angular.z = 0.0
        elif action == 2: # Right
            vel_cmd.linear.x = 1.0
            vel_cmd.angular.z = -1.5
        
        return vel_cmd

    def find_centroid(self, cv_image, height, width):
        lower_bound = np.array([99, 60, 60])
        upper_bound = np.array([120, 255, 255])
        x_centroid = -1
        y_centroid = -1

        ## @brief crop image to just bottom quarter
        cv_image =  cv_image[int(3*height/4):int(height), 0:int(width)]

        ## @brief Convert to HSV
        cv_image = cv2.cvtColor(cv_image, cv2.COLOR_BGR2HSV)

        ## @brief Removes holes in binary threshold output without introducing gradient
        cv_image = cv2.GaussianBlur(cv_image, (5,5), 15)
        
        ## @brief Threshold masking to make only the path white
        mask = cv2.inRange(cv_image, lower_bound, upper_bound)

        ## @brief Find centroid of the white path; prevents division by zero
        Moment = cv2.moments(mask, binaryImage = True)
        if (Moment['m00'] != 0):
            x_centroid = float(Moment['m10']/Moment['m00'])
            y_centroid = float(Moment['m01']/Moment['m00']) + int(3*height/4)

        return x_centroid, y_centroid

    def process_reward(self, action, truncated):
        if action == 0: # Left
            reward = 4
        elif action == 1: # Forward
            reward = 5
        elif action == 2: # Right
            reward = 4
        
        if truncated:
            reward = -300
        
        return reward

    def process_obs(self, obs: RosImage, state_space):
        NUM_BINS = state_space.n

        cv_image = CvBridge().imgmsg_to_cv2(obs, desired_encoding='bgr8')
        
        height, width, _ = cv_image.shape

        x_centroid, y_centroid = self.find_centroid(cv_image, height, width)

        if x_centroid == -1:
            truncated = True
            state = -1
        else:
            truncated = False
            idx = int((x_centroid * NUM_BINS) // width)
            idx = np.clip(idx, 0, NUM_BINS-1)
            state = idx

        reward = self.process_reward(state, truncated)

        return state, reward, truncated

    # Shutting down ROS2
    def user_close(self):
        self.ros_node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()