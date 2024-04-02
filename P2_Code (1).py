import random

import time
import sys
sys.path.append('../')

from Common_Libraries.p2_sim_lib import *

import os
from Common_Libraries.repeating_timer_lib import repeating_timer

def update_sim ():
    try:
        arm.ping()
    except Exception as error_update_sim:
        print (error_update_sim)

arm = qarm()
update_thread = repeating_timer(2, update_sim)


#these are global variables which will be accessed by the functions and will be described in further detail later
ID = 0
taken_IDs = []
gripper_state = "open"
red_autoclave_state = -1
green_autoclave_state = -1
blue_autoclave_state = -1

#ID 0 = home, ID 7 = pickup, IDs 1-6 represent the different autoclave bins
def identify_bin_location(id):
    if id == 1:
        return -0.608, 0.246, 0.414 #function returns coordinates to autoclave #1

    elif id == 2:
        return 0.0, -0.656, 0.414 #function returns coordinates to autoclave #2

    elif id == 3:
        return 0.0, 0.656, 0.414 #function returns coordinates to autoclave #3

    elif id == 4:
        return -0.418, 0.194, 0.188 #function returns coordinates to autoclave #4

    elif id == 5:
        return 0.0, -0.465, 0.149 #function returns coordinates to autoclave #5

    else:
        return 0.0, 0.465, 0.149 #function returns coordinates to autoclave #6

def move_end_effector(id):
    if id == 7: #if the id is set to pickup, the arm moves to the pickup location
        arm.move_arm(0.534, 0.0, 0.044)
    else: #runs the following if the id corresponds to an autoclave bin
        x, y, z = identify_bin_location(id) #retrieves assigned coordinates for the id
        arm.move_arm(x,y,z) #moves arm to the retrieved coordinates

def toggle_gripper():
    global gripper_state, ID
    #when this function is called and the gripper is open, the gripper closes and the variable changes to match the state. The opposite happens when the gripper is closed
    if gripper_state == "open":
        arm.control_gripper(32)
        gripper_state = "closed"
    else:
        arm.control_gripper(-32)
        gripper_state = "open"
    time.sleep(1)
    #the loop ends here for the small autoclave bins, so the arm returns to home position and the ID is rerolled
    if ID <= 3 and gripper_state == "open":
        taken_IDs.append(ID)
        arm.home()
        time.sleep(1)
        reroll_ID()
        #If the autoclave bin is large, the gripper needs to be moved out of the way before closing the bin
    elif ID >= 3 and gripper_state == "open":
        arm.home()

def toggle_autoclave_bin():
    global red_autoclave_state, green_autoclave_state, blue_autoclave_state, ID
    #the open_X_autoclave funcions require booleans, the state of the autoclave drawers are saved as either 1 (open) or -1 (closed)
    #the state variables are then compared to zero to determine if they're open or closed. The 1,-1 method is used over strings to save make the if-else statements concise 
    if ID == 4:
        red_autoclave_state *= -1   #opening autoclave drawers if closed before container is moved, based on the container ID
        arm.open_red_autoclave(bool(red_autoclave_state > 0))
        time.sleep(2)
        if red_autoclave_state == -1:
        #once the bin is manually closed by the user, the loop ends for large autoclave bins. Arm returns to home position and the ID is rerolled
            taken_IDs.append(ID) #adding to the defined list
            arm.home()
            reroll_ID()
    elif ID == 5:
        green_autoclave_state *= -1
        arm.open_green_autoclave(bool(green_autoclave_state > 0))
        time.sleep(2)
        if green_autoclave_state == -1:
            taken_IDs.append(ID)
            arm.home()
            reroll_ID()
    elif ID == 6:
        blue_autoclave_state *= -1
        arm.open_blue_autoclave(bool(blue_autoclave_state > 0))
        time.sleep(2)
        if blue_autoclave_state == -1:
            taken_IDs.append(ID)
            arm.home()
            reroll_ID()

def reroll_ID():
    #if there are no more tools to put away, this function is skipped entirely when called to prevent error.
    #The main function will then end the program.
    if len(taken_IDs) < 6:
        global ID, taken_IDs
        ID = random.randint(1,6)  #random generation of an ID that is associated with a specific container
        while ID in taken_IDs:
            ID = random.randint(1,6)
        arm.spawn_cage(ID)
        move_end_effector(7)
        print(len(taken_IDs))
        time.sleep(2)




'''
MAIN FUNCTION
'''

def main(): #this is the function that utilizes the combination of muscle sensor emulators
    reroll_ID()

    while True:
        #if there are no more tools to put away, the program terminates.
        if len(taken_IDs) == 6: #there are 6 different ID's
            arm.home()
            break
        else:
            #if both the left and right sensors are extended beyond threshold value
            if arm.emg_left() >= 0.4 and arm.emg_right() >= 0.4:
               toggle_autoclave_bin()
               time.sleep(1)
            #if only the left sensor is triggered, the program moves to the next required location
            elif arm.emg_left() >= 0.4 and arm.emg_right() < 0.4:
                move_end_effector(ID)
                time.sleep(1)
            #if only the right sensor is triggered, the gripper opens/closes
            elif arm.emg_left() < 0.4 and arm.emg_right() >=0.4:
                toggle_gripper()   
                time.sleep(1)
           
main()


