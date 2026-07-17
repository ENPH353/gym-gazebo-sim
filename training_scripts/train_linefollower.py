#!/usr/bin/env python3
import random
import gym_gazebo
import gymnasium as gym
import numpy as np
from torch.utils.tensorboard.writer import SummaryWriter

def main():
    writer = SummaryWriter()
    env = gym.make('LineFollowerEnv-v0')

    observation_space = env.observation_space
    action_space = env.action_space

    epsilon = 0.8
    alpha = 0.1
    gamma = 0.9

    q_table = np.zeros((observation_space.n, action_space.n))

    try:
        state, _ = env.reset()
        action = choose_action(state, q_table, epsilon, action_space)
        for episode in range(1000):
            total_reward = 0
            done = False

            while not done:
                action = choose_action(state, q_table, epsilon, action_space)
                next_state, reward, terminated, truncated, _ = env.step(action)
                done = terminated or truncated

                # Update Q-table using the Q-learning formula
                current_value = q_table[state, action]
                best_future_value = np.max(q_table[next_state])
                q_table[state, action] = current_value + alpha * (reward + gamma * best_future_value - current_value)

                state = next_state
                total_reward += reward

            env.reset()
            epsilon = max(0.01, epsilon * 0.99)  # Decay epsilon
            print(f"Episode {episode}: Total Reward: {total_reward}")
            writer.add_scalar("Total Reward", total_reward, episode)

    except KeyboardInterrupt:
        print("Training interrupted by user!")
    
    finally:
        env.close()
        writer.flush()
        writer.close()

def choose_action(state, q_table, epsilon, action_space):
    if random.random() < epsilon:
        # Explore
        action = action_space.sample()
    else:
        # Exploit
        q_values = q_table[state]
        max_q = np.max(q_values)
        
        # np.where returns an array of indices where the condition is true
        best_actions = np.where(q_values == max_q)[0]
        
        # Randomly select one of the tied best actions
        action = np.random.choice(best_actions)
    
    return action

if __name__ == "__main__":
    main()