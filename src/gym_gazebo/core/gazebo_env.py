import os
import time
import subprocess

import gymnasium as gym
from gymnasium.utils import seeding
from ament_index_python.packages import get_package_prefix

# Gazebo Transport Imports
from gz.msgs10.world_control_pb2 import WorldControl
from gz.transport13 import Node as GzNode
from gz.msgs10.int32_pb2 import Int32
from gz.msgs10.boolean_pb2 import Boolean

class GazeboEnv(gym.Env):
    def __init__(self, launch_pkg, launch_file, world_name):
        # Passing arguments to parent class
        super(GazeboEnv, self).__init__()

        print(f"Launching {launch_file} from {launch_pkg}.")

        # Copy the terminal environment
        terminal_env = os.environ.copy()

        plugin_pkg_install_path = get_package_prefix('custom_plugins')
        plugin_lib_path = os.path.join(plugin_pkg_install_path, 'lib')
        
        if "GZ_SIM_SYSTEM_PLUGIN_PATH" in terminal_env:
                terminal_env["GZ_SIM_SYSTEM_PLUGIN_PATH"] += f":{plugin_lib_path}"
        else:
            terminal_env["GZ_SIM_SYSTEM_PLUGIN_PATH"] = plugin_lib_path


        # Launch gazebo using the launch file
        self.sim_process = subprocess.Popen(
            ["ros2", "launch", launch_pkg, launch_file],
            env=terminal_env,            
            stderr=subprocess.STDOUT,      
            preexec_fn=os.setsid          
        )

        # Buffer to wait for Gazebo to finish booting
        time.sleep(4.0)

        # Setting up Gazebo nodes
        self.gz_node = GzNode()

        # Gazebo topics
        reset_topic = "/keyboard/keypress"
        self.world_control_service = f"/world/{world_name}/control"

        # Setting up reset node
        self.pub_reset_msg = self.gz_node.advertise(reset_topic, Int32)
        self.reset_msg = Int32(data=114)

        print("Simulation ready!")
    

    # MAIN FUNCTIONS
    def step(self, action):
        raise NotImplementedError
    
    def reset(self, seed=None, options=None):
        raise NotImplementedError
    
    def user_close(self): 
        raise NotImplementedError
    
    def close(self):
        # Run user logic first
        self.user_close()

        # Terminate the Gazebo process
        subprocess.run(["pkill", "-f", "gz sim"])
        subprocess.run(["pkill", "-f", "gz sim server"])
        subprocess.run(["pkill", "-f", "gzsim gui"])   
        subprocess.run(["pkill", "-9", "-f", "ros_gz_bridge"])
        subprocess.run(["pkill", "-9", "-f", "ros2 launch"])

    # HELPER FUNCTIONS
    def _seed(self, seed=None):
        self.np_random, seed = seeding.np_random(seed)
        return [seed]
    
    def _pause_sim(self, pause: bool):
        # Creating message request
        sim_pause_req = WorldControl()
        sim_pause_req.pause = pause


        # Sending request to Gazebo server
        result, response = self.gz_node.request(
            self.world_control_service,
            sim_pause_req,
            WorldControl,
            Boolean,
            10 # Maximum timeout
        )
    
    def _step_physics(self, iterations: int):
        # Creating stepping message request
        sim_step_req = WorldControl()
        sim_step_req.pause = True
        sim_step_req.multi_step = iterations

        # Sending request to Gazebo server
        result, response = self.gz_node.request(
            self.world_control_service,
            sim_step_req,
            WorldControl,
            Boolean,
            10 # Maximum timeout
        )
    
    def _reset_agents(self):
        # Sending the reset message
        self.pub_reset_msg.publish(self.reset_msg)