from gymnasium.envs.registration import register

register(
    id='GazeboEnv-v0',                                      
    entry_point='gym_gazebo.core.gazebo_env:GazeboEnv',
    max_episode_steps=500,                                   
)