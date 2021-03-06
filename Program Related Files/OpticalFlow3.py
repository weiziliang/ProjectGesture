import numpy as np
import cv2
import time
import math
from PIL import Image
from resizeimage import resizeimage
from playsound import playsound

lk_params = dict( winSize  = (100,100),
                  maxLevel = 2,
                  criteria = (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 10, 0.03))


color = np.array([255,255,255])
kernel = np.ones((15,15),np.uint8)

def check_out_of_radius(x,y,new,r):   #Check new is within the circle of radius r drawn with (x,y) as centre
    x1 = new[0][0]
    y1 = new[0][1]
    dist = math.sqrt((x-x1)**2+(y-y1)**2)
    if dist<r:
        return 0
    else:
        return 1


start_time_up = 0
elapsed_time_up = 0
previous_point = 0
next_point = 0
def check_if_stationary(new,t):    #check if point is stationary by checking its coordinates after regular 't' intervals of time
    global previous_point
    global next_point
    global start_time_up
    global elapsed_time_up
    if elapsed_time_up == 0:
        start_time_up = time.time()
        previous_point = new
    elapsed_time_up = time.time()-start_time_up
    if elapsed_time_up>=t:
        elapsed_time_up = 0
        next_point = new
        x1 = previous_point[0][0]
        y1 = previous_point[0][1]
        x2 = next_point[0][0]
        y2 = next_point[0][1]
        dist = math.sqrt((x1-x2)**2+(y1-y2)**2)
        if dist<=5:
            return 1
        else:
            return 0
    elif elapsed_time_up<t:
        return 0

def length_of_line(coordinates):    #To check the length of path traversed by cursor(only called by check_if_digit)
    length = 0
    for t in range(len(coordinates)-1):
        x1 = coordinates[t][0][0]
        y1 = coordinates[t][0][1]
        x2 = coordinates[t+1][0][0]
        y2 = coordinates[t+1][0][1]
        length = length + math.sqrt((x1-x2)**2+(y1-y2)**2)
    return length


digit_cood = []
return_cood = []
def check_if_digit(new,is_stationary):
    global digit_cood
    global return_cood
    digit_cood.append(new)
    if is_stationary==1:
        distance = length_of_line(digit_cood)
        if distance>=100:
            return_cood = digit_cood
            digit_cood = []
            return 1,return_cood          #Digit is drawn
        else:
            digit_cood = []
            return 0,return_cood         #Digit is not drawn
    else:
        return -1,return_cood                   #Still Detecting


digit_count = 0
def save_image(img,coordinates):   #Save image with digit at centre and perform morphological operations to enhance digit prediction
    global digit_count
    top_most_cood = 480
    bottom_most_cood = 0
    left_most_cood = 640
    right_most_cood = 0
    for t in range(len(coordinates)-1):
        x1 = coordinates[t][0][0]
        y1 = coordinates[t][0][1]
        if x1<left_most_cood:
            left_most_cood = x1
        if x1>right_most_cood:
            right_most_cood = x1
        if y1<top_most_cood:
            top_most_cood = y1
        if y1>bottom_most_cood:
            bottom_most_cood = y1
    if top_most_cood-30<0:
        y2 = 0
    else:
        y2 = top_most_cood-30
    if bottom_most_cood+30>480:
        y3 = 480
    else:
        y3 = bottom_most_cood+30
    if left_most_cood-100<0:
        x2 = 0
    else:
        x2 = left_most_cood-100
    if right_most_cood+100>640:
        x3 = 640
    else:
        x3 = right_most_cood+100
    crop_img = img[int(y2):int(y3), int(x2):int(x3)]
    dilated_img = cv2.dilate(crop_img,kernel,iterations = 1)
    ret,inv_img = cv2.threshold(dilated_img,127,255,cv2.THRESH_BINARY_INV)
    #inv_img = cv2.flip(inv_img,1)
    cv2.imwrite('Digits/'+str(digit_count)+'.png',inv_img)
    with open('Digits/'+str(digit_count)+'.png', 'r+b') as f:
        with Image.open(f) as image:
            cover = resizeimage.resize_cover(image, [28, 28])
            cover.save('Digits/'+str(digit_count)+'.png', image.format)
            digit_count = digit_count + 1
            playsound('/home/apoorv/Desktop/Final/Attempt 6/sound.wav')
    
frame_counter = 0
def main(x,y):
    cap_flow = cv2.VideoCapture(0)
    ret, old_frame = cap_flow.read()
    old_gray = cv2.cvtColor(old_frame, cv2.COLOR_BGR2GRAY)
    p0 = np.array([[[x,y]]],np.float32)
    mask = np.zeros_like(old_frame)
    #0 refers to False and 1 refers to True
    out_of_radius = 0
    is_stationary = 0
    digit_is_drawn = 0
    setting_up_next_digit = 0
    is_stationary_next_digit = 0
    out_of_radius_next_digit = 0
    global frame_counter
    playsound('/home/apoorv/Desktop/Final/Attempt 6/sound.wav')
    while(True):
        ret,frame = cap_flow.read()
        frame_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        p1, st, err = cv2.calcOpticalFlowPyrLK(old_gray, frame_gray, p0, None, **lk_params)
        good_new = p1[st==1]
        good_old = p0[st==1]
        t1,t2 = good_old.shape
        if t1 == 0:
            playsound('/home/apoorv/Desktop/Final/Attempt 6/sound.wav')
            cap_flow.release()
            break
        if setting_up_next_digit == 1:
            out_of_radius_next_digit = check_out_of_radius(x,y,good_new,20)
            if out_of_radius_next_digit == 1:
                is_stationary_next_digit = check_if_stationary(good_new,0.2)
                if is_stationary_next_digit == 1:
                    x = good_new[0][0]
                    y = good_new[0][1]
                    setting_up_next_digit = 0
        elif out_of_radius == 0:
            out_of_radius = check_out_of_radius(x,y,good_new,20)
        elif out_of_radius == 1:
            is_stationary = check_if_stationary(good_new,0.2)
            digit_is_drawn,digit_cood = check_if_digit(good_new,is_stationary)
            if digit_is_drawn == 1:
                save_image(mask,digit_cood)
                mask = np.zeros_like(old_frame)
                setting_up_next_digit = 1
                x = good_new[0][0]
                y = good_new[0][1]
                out_of_radius = 0
            elif digit_is_drawn == 0 :
                x = good_new[0][0]
                y = good_new[0][1]
                out_of_radius = 0
                mask = np.zeros_like(old_frame)

        if p1 is not None:
            if setting_up_next_digit == 0:
                for i,(new,old) in enumerate(zip(good_new,good_old)):
                    a,b = new.ravel()
                    c,d = old.ravel()
                    mask = cv2.line(mask, (a,b),(c,d), color, 2)
            #cv2.circle(mask,(x,y), 20, (0,0,255), -1)    #Drawing a circle for testing purposes
            img = cv2.add(frame,mask)
            #cv2.imshow('mask',mask)
            cv2.imshow('frame',img)
            old_gray = frame_gray.copy()
            p0 = good_new.reshape(-1,1,2)
            frame_counter=frame_counter+1
        if cv2.waitKey(1) == 27:
            break

time.sleep(2)
main(320,240)
