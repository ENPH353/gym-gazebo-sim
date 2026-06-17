import cv2
import numpy as np
from cv_bridge import CvBridge
from geometry_msgs.msg import Twist as RosTwist
from sensor_msgs.msg import Image as RosImage

def process_action(action: int):
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

def find_centroid(cv_image, height, width):
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

def process_reward(action, truncated):
    if action == 0: # Left
        reward = 4
    elif action == 1: # Forward
        reward = 5
    elif action == 2: # Right
        reward = 4
    
    if truncated:
        reward = -300
    
    return reward

def process_obs(obs: RosImage, state_space):
    NUM_BINS = state_space.n

    cv_image = CvBridge().imgmsg_to_cv2(obs, desired_encoding='bgr8')
    
    height, width, _ = cv_image.shape

    x_centroid, y_centroid = find_centroid(cv_image, height, width)

    if x_centroid == -1:
        truncated = True
        state = -1
    else:
        truncated = False
        idx = int((x_centroid * NUM_BINS) // width)
        idx = np.clip(idx, 0, NUM_BINS-1)
        state = idx

    reward = process_reward(state, truncated)

    return state, reward, truncated
