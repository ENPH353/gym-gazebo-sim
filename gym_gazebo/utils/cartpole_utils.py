def calculate_reward(terminated):
    if not terminated:
        reward = 1.0
    else:
        reward = 0
    
    return reward

def process_obs(obs, x_limit, theta_limit):
    theta = obs[0]
    x = obs[1]
    terminated = False

    if abs(theta) > theta_limit or abs(x) > x_limit:
        terminated = True
    
    reward = calculate_reward(terminated)

    return reward, terminated

def process_action(action, x_vel):
    if action == 1:
        cmd_vel = x_vel + 0.2
    else:
        cmd_vel = x_vel - 0.2
    
    return cmd_vel