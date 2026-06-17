from .core.gazebo_env import GazeboEnv
from .envs.cartpole_env import CartpoleEnv
from gymnasium.envs.registration import register

register(
    id='CartpoleEnv-v0',                                      
    entry_point='gym_gazebo.envs.cartpole_env:CartpoleEnv',
    max_episode_steps=500,                                   
)