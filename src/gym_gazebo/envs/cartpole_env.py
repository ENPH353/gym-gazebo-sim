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

class CartpoleEnv(GazeboEnv):
    def __init__(self):
        # Intializing ROS2
        rclpy.init(args=None)

        # Passing arguments to parent class
        super(CartpoleEnv, self).__init__(launch_pkg='cartpole_ros',
                                          launch_file='my_cartpole.launch.xml',
                                          world_name='cartpole_world')

        # Setting up ROS2 nodes
        self.ros_node = RosNode('cartpole_RL')

        # Initializing variables
        self.is_resetting = False
        self.latest_obs = None
        self.new_obs_event = False
        self.theta_limit_rad = 12 * math.pi / 180
        self.x_limit = 15

        # Setting the observation and action spaces
        low_bounds = np.array([-self.theta_limit_rad * 2,
                                -15, -np.inf, -np.inf], dtype=np.float32)
        high_bounds = np.array([self.theta_limit_rad * 2, 15, 
                                np.inf, np.inf], dtype=np.float32)
        self.observation_space = gym.spaces.Box(low=low_bounds, 
                                                high=high_bounds, 
                                                dtype=np.float32)
        self.action_space = gym.spaces.Discrete(2)

        # ROS2 topics
        observation_topic = "/joint_states"
        velocity_topic = "/cart_velocity_controller/commands"

        # Publishing and subscribing to ROS2 topics
        self.pub_cmd_vel_msg = self.ros_node.create_publisher(
            Float64MultiArray, velocity_topic, 10)
            
        self.sub_obs = self.ros_node.create_subscription(
            JointState, observation_topic, self.obs_feed_, 10)
        
        self.current_vel = 0
        self.latest_obs = None
        self.SPIN_TIME_s = 0.01
    
    ## OBSERVATION CALLBACK

    def obs_feed_(self, msg: JointState):
        # Takes in observation, returns a flag an observation is recieved
        if not self.is_resetting:
            # INDEX:
                # 0: pole angle (rad)
                # 1: cart position (m)
                # 2: pole angular velocity (rad/s)
                # 3: cart velocity (m/s)
            self.latest_obs = np.concatenate([msg.position, 
                                              msg.velocity]).astype(np.float32)
            
            self.new_obs_event = True

            # Use atan(tan()) to bound theta to [-2pi; +2pi] values
            theta = math.atan(math.tan(self.latest_obs[0]))
            x = self.latest_obs[1]
            theta_dot = self.latest_obs[2]
            x_dot = self.latest_obs[3]

            self.latest_state = [round(x, 2), round(x_dot, 2), 
                                 round(theta, 2), round(theta_dot, 2)]

    ## MAIN FUNCTIONS:

    def reset(self, seed=None, options=None):
        """!
        @brief resets the environment: zero joint positions and velocities
        @param seed
        @param options
        @return state of the system after reset
        """
        self.is_resetting = True
        # print("*** RESETTING...")

        # Unpause the sim
        self._pause_sim(False)

        # Zero out velocities
        self.current_vel = 0
        vel_cmd = Float64MultiArray()
        vel_cmd.data = [self.current_vel]
        self.pub_cmd_vel_msg.publish(vel_cmd)

        # Reset position and joints
        self._reset_agents()
        self.is_resetting = False

        #print("RESET: Waiting for new data...")

        # Wait for next observation to come in
        data = self.latest_obs
        while data is None:
            # Telling executor (node) to spin
            rclpy.spin_once(self.ros_node, timeout_sec=self.SPIN_TIME_s)
            data = self.latest_obs
        self.latest_obs = None

        #print("RESET: Acquired new data.")

        # Pause the sim
        self._pause_sim(True)

        self.print_state("Reset: ", self.latest_state)

        # Zero position and speed (speed up learning)
        simpler_state = [0, 0, self.latest_state[2], self.latest_state[3]]

        return simpler_state, {}

    def step(self, action: int):
        """!
        @brief Takes one simulation step
        @param action (int): acceleration value
        @return A tuple containing:
            - **observation** (tuple of floats): theta, x, theta_dot, x_dot
            - **reward** (float): 0 for episode done. 1 otherwise
            - **terminated** (bool): _True_ episode is done. _False_ otherwise
            - **other** (dictionary): catch all variable for other data
        """
        # print("STEP...")
        # Process the action
        self.current_vel += 0.2 if action == 1 else -0.2

        # Creating the velocity command
        vel_cmd = Float64MultiArray()
        vel_cmd.data = [self.current_vel]

        # Unpause the sim
        self._pause_sim(False)

        # Moving the agent
        self.pub_cmd_vel_msg.publish(vel_cmd)

        # Leave running until next observation comes in
        data = self.latest_obs
        while data is None:
            rclpy.spin_once(self.ros_node, timeout_sec=self.SPIN_TIME_s)
            data = self.latest_obs
        self.latest_obs = None

        # Pause the simulation after the next observation comes in
        self._pause_sim(True)

        reward, terminated = self.process_obs(self.latest_state, 
                                              self.x_limit, 
                                              self.theta_limit_rad)

        self.print_state("Step: ", self.latest_state)

        # Zero position and speed (speed up learning)
        simpler_state = [0, 0, self.latest_state[2], self.latest_state[3]]

        truncated = False # We don't use this variable but we need to return it
        return simpler_state, reward, terminated, truncated, {}


    ### HELPER FUNCTIONS:

    def process_obs(self, state, x_limit, theta_limit):
        """!
        @brief process an observation 
        """
        x_abs     = abs(state[0])
        theta_abs = abs(state[2])
        terminated = False

        if theta_abs > theta_limit:
            print("Angle exceeded {:.2f} > {:.2f} rad".
                  format(theta_abs, theta_limit))
            terminated = True

        if x_abs > x_limit:
            print("Position exceeded {:.2f} > {:.2f} m".
                  format(x_abs, x_limit))
            terminated = True
        
        reward = 1.0 if not terminated else 0.0

        return reward, terminated

    def print_state(self, msg=None, state=[0, 0, 0, 0]):
        """!
        @brief print state formated nicely
        @param state (tuple of floats)
        """
        return
        print(msg, "x: {:.3f} | x_dot: {:.3f} | "
            "theta: {:.3f} | theta_dot: {:.3f}".format(
            state[0], state[1], 
            state[2], state[3]))


    # Shutting down ROS2
    def user_close(self):
        self.ros_node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()