from gymnasium.envs.registration import register

register(
    id='CartpoleEnv-v0',                                      
    entry_point='gym_gazebo.envs.cartpole_env:CartpoleEnv',
    max_episode_steps=500,                                   
)