import time
import picamera
import RPi.GPIO as GPIO  # new
import atexit
import random as r
import subprocess
import sys

GPIO.setmode(GPIO.BCM)  # new
GPIO.setup(18, GPIO.IN, GPIO.PUD_DOWN)  #photo trigger
GPIO.setup(23,GPIO.IN,GPIO.PUD_DOWN)    #Gif trigger
GPIO.setup(24,GPIO.IN,GPIO.PUD_DOWN)    #off button
GPIO.setup(25,GPIO.OUT)

GPIO.output(25,False)                   #feedback lights

incrementCounter = 0
counterFileName = 'counter.txt'
offSwitch =0

# function takes 10 photos with png extension then runs image magick, as a subprocess to avoid
#stopping program flow, to take every second photo and stich them into a gif. 
## with some basic testing this was the fatest way to take the photos
#with big enough gaps to pick up decent movement
#The imageMagick stiching takes about 15sec, taking another image in this period 
#overwrites the existing files and ruins the gif. Their are better ways to do this but it worked for me.

def takeGif():
    with picamera.PiCamera() as camera:
        GPIO.output(25,True)
        time.sleep(1) #let the camera settle and adjust to light
        camera.resolution = (576,384)
        camera.framerate = 30
        camera.capture_sequence([
            '/home/pi/projects/piCamera/pics/gif/image1.png',
            '/home/pi/projects/piCamera/pics/gif/imagea.jpg',
            '/home/pi/projects/piCamera/pics/gif/image2.png',
            '/home/pi/projects/piCamera/pics/gif/imageb.jpg',
            '/home/pi/projects/piCamera/pics/gif/image3.png',
            '/home/pi/projects/piCamera/pics/gif/imagec.jpg',
            '/home/pi/projects/piCamera/pics/gif/image4.png',
            '/home/pi/projects/piCamera/pics/gif/imaged.jpg',
            '/home/pi/projects/piCamera/pics/gif/image5.png'
                ], use_video_port=True)
    subprocess.Popen("gm convert -delay 10 /home/pi/projects/piCamera/pics/gif/*.png /home/pi/projects/piCamera/pics/gif/joined{0}.gif".format(incrementCounter), shell=True)    
    GPIO.output(25,False)

# clean up the GPIO's
def cleanUp():
    GPIO.cleanup()
    print("gracefull exit")

# takes a photo with a random delay between shutter and capture - just because - and stores it with a counter
# filename to avoid overwriting. This counter is written to a txt file to make sure photo's arent overwritten
# when the camera is turned on and off
def takePhoto():
    GPIO.output(25, True)
    with picamera.PiCamera() as camera:
        random = 0.0
        random = r.uniform(0.1,2) # this affects the auto iso and wb - less time means lees time to run auto calibration
        time.sleep(random)
        camera.capture('/home/pi/projects/piCamera/pics/image{0}.jpg'.format(incrementCounter),use_video_port=True)
        print("took photo")
        GPIO.output(25,False)

	
def debug(channel):
    print("triggered");
	
# when program starts, open the counter txt file and load the counter number stored their.
# this is appended to the photo, incremented, and written to the text file to keep track of the photos taken
# and avoid overwritting images
def loadIncrementCounter():
    try:
        inputFile = open(counterFileName, 'rt')
        for line in inputFile:
            i = int(line)
        global incrementCounter 
        incrementCounter = i
        print(incrementCounter)
    finally:
        inputFile.close()
	

#save increment counter to a txt file , over write it everytime a photo is taken
def saveIncrementCounter(incrementCounterValue):
    try:
        inputFile = open(counterFileName, 'wt')
        inputFile.write(str(incrementCounterValue))
        print("just wrote counter file name {0} to text file {1}".format(incrementCounterValue,counterFileName))
    finally:
        inputFile.close

# to turn of the camera, press the power button three times.
def shutdownRoutine(channel):
    global offSwitch
    offSwitch = offSwitch+1
    print(offSwitch)
    for i in range(0,5):
        GPIO.output(25,True)
        time.sleep(0.1)
        GPIO.output(25,False) 
        time.sleep(0.1)

def mainGif(channel):    
    global incrementCounter
    incrementCounter+=1
    takeGif()
    global incrementCounter
    saveIncrementCounter(incrementCounter)


def mainPhoto(channel):
    global incrementCounter
    incrementCounter+=1
    takeGif()
    global incrementCounter
    saveIncrementCounter(incrementCounter)


def shutdown():
    GPIO.output(25,True)
    time.sleep(5) # if there is any gif processing happening, wait abit to finish
    GPIO.output(25,False)
    subprocess.Popen("sudo halt", shell=True)    
    sys.exit()    

#all the buttons use intterupts and threaded callbacks
GPIO.add_event_detect(18,GPIO.RISING,callback = mainPhoto,bouncetime = 500)
GPIO.add_event_detect(23,GPIO.RISING,callback = mainGif,bouncetime = 500 )
GPIO.add_event_detect(24,GPIO.RISING,callback = shutdownRoutine,bouncetime = 500 )

#if the program is exited, call the cleanUp function
atexit.register(cleanUp)

loadIncrementCounter()

# when the power button has been pressed three times, close the program and shutdown the RPi
while True:
    global offSwitch
    if offSwitch == 3:
        shutdown()   
    
        

     

