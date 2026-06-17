# Gym-Gazebo-Sim

Gym-Gazebo-Sim is a simple wrapper and Gazebo plugin that extends the Gymnasium API for Gazebo Sim Harmonic and ROS2 Jazzy for developers and researchers seeking to use Gazebo Sim for reinforcement learning.
## Description

Gym-Gazebo-Sim provides an abstract class with helper methods called `GazeboEnv` which communicates with Gazebo Sim's internal transport network. This enables developers to inherit the class to create their own environments without having to interface directly with Gazebo Sim internal structure.

The API also provides a ros2 workspace that comes installed with packages for prebuilt environments and a C++ reset plugin that users can call which teleports all non-static entities back to their starting positions.
#### Features:
- Currently, the API provides an abstract class called `GazeboEnv` that inherits the standard gymnasium `Env` class with the following helper methods added:

> **Method:** `_pause_sim(self, pause: bool)`
>
> **Usage:** Pauses and resumes the Gazebo simulation.
> 
> **Parameters:**
> * `pause` (bool): Set to `True` to freeze simulation physics; set to `False` to resume normal simulation. 

<br/>

> **Method:** `_step_physics(self, iterations: int)`
>
> **Usage:** Advances the Gazebo simulation clock forward by a specific number of steps whilst keeping the simulation otherwise paused.
> 
> **Parameters:**
> * `iterations` (int): The number of individual physics steps the simulator should execute before pausing.

<br/>

> **Method:** `_reset_agents(self)`
>
> **Usage:** Instantly resets the environment's agents back to their starting poses and joint states using a custom reset plugin that is built as a package in `ros2_ws`.
> 
> **Parameters:**
> * *None*

<br/>

> **Method:** `user_close(self)`
>
> **Usage:** An abstract placeholder method that is designed to force child subclasses inheriting from `GazeboEnv` to define its own cleanup behaviour (*i.e.: shutting down ros2 nodes*).
> 
> **Parameters:**
> * *None*

<br/>

> **Method:** `close(self)`
>
> **Usage:** First executes user-defined shutdown logic written in `user_close()` and then terminates all Gazebo simulator instances, GUI instances, and ros2 bridges and launch processes. 
> 
> **Parameters:**
> * *None*

- The API also provides a ros2 package inside `ros2_ws/src/` called `custom_plugins` that houses a reset plugin that directly communicates with Gazebo Sim to find all non-static entities and teleports them to their original spawn positions and joint states.
  
  The plugin can be added to any custom workspace by just copy and pasting the package directory (see install instructions) into your own ros2 workspace folder, and then adding the following tags to your `.sdf`:
  
```
<plugin
  filename="libResetSimPlugin.so"
  name="reset::ResetSimPlugin">
</plugin>
```

- In addition to the prebuilt environments are two training scripts that are available for demo inside the `training_scripts/` directory. These can be run as normal python scripts using the terminal.

## Getting Started

### Pre-Requisites
* **OS:** Ubuntu 24.04
* **ros2:** Jazzy Jalisco
* **Python:** 3.10+
* **Core Dependencies:** Gymnasium 1.3.0+, Numpy 1.26+
### Installation
This project requires compiling both Python libraries and ros2 packages. We have provided a script to handle this.

**1. Source or create a ros accessible virtual environment**
- The `--system-site-packages` flag will enable the virtual environment access the global ros2 `rclpy` libraries
```
(Inside your own desired venvs folder)
python3 -m venv your_venv_name --system-site-packages
```
**2. Clone the repository**
```
(Inside your own desired install folder)
git clone https://github.com/SniperReborn/gym-gazebo-sim.git

cd gym_gazebo_sim
```

**3. Run the installation script
```
./install.sh
```

**4a. (Optional) Sourcing the API's prebuilt ros2 workspace:**
- This step is required if you want to use the prebuilt environments that `gym-gazebo-sim` offers.

```
(Inside the root folder gym_gazebo_sim)
source ros2_ws/install/setup.bash
```

**4b. (Optional) Importing the custom reset plugin:**
- This step is required for users that want to build their own environment using `gym_gazebo_sim` since the API uses a custom reset plugin that teleports all non-static entities back to their spawn points.
- The command below will copy the API's `custom_plugins` package to your ros2 workspace's source folder.

```
(Inside the root folder gym_gazebo_sim)
cp -r ros2_ws/src/custom_plugins/ /path/to/your/workspace/src/
```

- To enable the plugin for your world, simply add the following lines inside the `<world></world>` tags of your `.sdf` world file:
```
<plugin
	filename="libResetSimPlugin.so"
	name="reset_plugin::ResetSimPlugin">
</plugin>
```
### Usage Examples:

- This example shows how to use the prebuilt environments that the API comes with:
```
import rclpy
import gymnasium as gym
import gym_gazebo

def main():
	
	# When run, the API will automatically launch Gazebo
	with the cartpole environment and ros2
	env = gym.make('CartpoleEnv-v0')
	
	try:
		obs, _ = env.reset()
		for _ in range(1000):
			action = env.action_space.sample()
			obs, reward, termianted, truncated, info = env.step(action)
		
		if terminated or truncated:
			obs, _ = env.reset()
	
	except KeyboardInterrupt:
		print("Stopped training")
	finally:
		env.close()
	
```

- This example shows how to inherit from the `GazeboEnv` class to make your own environment:
```
import gymnasium as gym
from gym_gazebo import GazeboEnv

class CustomEnv(GazeboEnv):
	super().__init__(
		launch_pkg='my_robot_launch_pkg',
		launch_file='my_robot.launch.xml',
		world_name='my_sdf_specified_world_name'
	)
	
	# Define your observation and action space here
	self.observation_space = gym.spaces.Discrete(4)
    self.action_space = gym.spaces.Discrete(2)
    
	def step(self, action):
		# Custom action publishing and processing logic
		
		# Unpause the sim and let the action play out
		self._pause_sim(False)   
		
		# Wait for next action
		
		# Pause the sim once the next observation comes in
		self._pause_sim(True)
		
		pass
	
	def reset(self):
		# Pause simulation during reset
		self._pause_sim(True)
		
		# Reset logic here. Maybe iterate the simulation three times!
		self._step_physics(3)
		
		# Unpause simulation
		self._pause_sim(False)
		
	def user_close(self):
		# Close down any ros2 nodes you made in this class or process observations.
```
## Help

Please email me at taigasery78@gmail.com for help or raise an issue on this GitHub page.
## Authors

- [Taiga Momose](https://www.linkedin.com/in/taiga-momose/)
- [Miti Isbasescu](https://projectlab.engphys.ubc.ca/location/)

## Version History

* 0.0.1
    * Initial Alpha release

## License

This project is licensed under the [MIT] License - see the LICENSE.md file for details

## Acknowledgments

**Inspiration and code snippets:**
* AcutronicRobotics for [gym-gazebo2](https://github.com/acutronicRobotics/gym-gazebo2)
* The Farama Foundation for [the Gymnasium API](https://github.com/farama-foundation/gymnasium)
* Google for coding assistance with [Google Gemini](https://gemini.google.com)


