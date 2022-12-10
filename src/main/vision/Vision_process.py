# Import the camera server
#!/usr/bin/env python3

# Copyright (c) FIRST and other WPILib contributors.
# Open Source Software; you can modify and/or share it under the terms of
# the WPILib BSD license file in the root directory of this project.

import json
import time
import sys

from cscore import CameraServer, VideoSource, UsbCamera, MjpegServer
from networktables import NetworkTablesInstance

import numpy as np
import cv2
from tkinter import *
from tkinter.ttk import *

#   JSON format:
#   {
#       "team": <team number>,
#       "ntmode": <"client" or "server", "client" if unspecified>
#       "cameras": [
#           {
#               "name": <camera name>
#               "path": <path, e.g. "/dev/video0">
#               "pixel format": <"MJPEG", "YUYV", etc>   // optional
#               "width": <video mode width>              // optional
#               "height": <video mode height>            // optional
#               "fps": <video mode fps>                  // optional
#               "brightness": <percentage brightness>    // optional
#               "white balance": <"auto", "hold", value> // optional
#               "exposure": <"auto", "hold", value>      // optional
#               "properties": [                          // optional
#                   {
#                       "name": <property name>
#                       "value": <property value>
#                   }
#               ],
#               "stream": {                              // optional
#                   "properties": [
#                       {
#                           "name": <stream property name>
#                           "value": <stream property value>
#                       }
#                   ]
#               }
#           }
#       ]
#       "switched cameras": [
#           {
#               "name": <virtual camera name>
#               "key": <network table key used for selection>
#               // if NT value is a string, it's treated as a name
#               // if NT value is a double, it's treated as an integer index
#           }
#       ]
#   }

configFile = "/boot/frc.json"

class CameraConfig: pass

team = None
server = False
cameraConfigs = []
switchedCameraConfigs = []
cameras = []
lowh = 0
lows = 0
lowv = 0

highh = 0
highs = 0
highv = 0

def parseError(str):
    """Report parse error."""
    print("config error in '" + configFile + "': " + str, file=sys.stderr)

def readCameraConfig(config):
    """Read single camera configuration."""
    cam = CameraConfig()

    # name
    try:
        cam.name = config["name"]
    except KeyError:
        parseError("could not read camera name")
        return False

    # path
    try:
        cam.path = config["path"]
    except KeyError:
        parseError("camera '{}': could not read path".format(cam.name))
        return False

    # stream properties
    cam.streamConfig = config.get("stream")

    cam.config = config

    cameraConfigs.append(cam)
    return True

def readSwitchedCameraConfig(config):
    """Read single switched camera configuration."""
    cam = CameraConfig()

    # name
    try:
        cam.name = config["name"]
    except KeyError:
        parseError("could not read switched camera name")
        return False

    # path
    try:
        cam.key = config["key"]
    except KeyError:
        parseError("switched camera '{}': could not read key".format(cam.name))
        return False

    switchedCameraConfigs.append(cam)
    return True

def readConfig():
    """Read configuration file."""
    global team
    global server

    # parse file
    try:
        with open(configFile, "rt", encoding="utf-8") as f:
            j = json.load(f)
    except OSError as err:
        print("could not open '{}': {}".format(configFile, err), file=sys.stderr)
        return False

    # top level must be an object
    if not isinstance(j, dict):
        parseError("must be JSON object")
        return False

    # team number
    try:
        team = j["team"]
    except KeyError:
        parseError("could not read team number")
        return False

    # ntmode (optional)
    if "ntmode" in j:
        str = j["ntmode"]
        if str.lower() == "client":
            server = False
        elif str.lower() == "server":
            server = True
        else:
            parseError("could not understand ntmode value '{}'".format(str))

    # cameras
    try:
        cameras = j["cameras"]
    except KeyError:
        parseError("could not read cameras")
        return False
    for camera in cameras:
        if not readCameraConfig(camera):
            return False

    # switched cameras
    if "switched cameras" in j:
        for camera in j["switched cameras"]:
            if not readSwitchedCameraConfig(camera):
                return False

    return True

def startCamera(config):
    """Start running the camera."""
    print("Starting camera '{}' on {}".format(config.name, config.path))
    inst = CameraServer.getInstance()
    camera = UsbCamera(config.name, config.path)
    server = inst.startAutomaticCapture(camera=camera, return_server=True)

    camera.setConfigJson(json.dumps(config.config))
    camera.setConnectionStrategy(VideoSource.ConnectionStrategy.kKeepOpen)

    if config.streamConfig is not None:
        server.setConfigJson(json.dumps(config.streamConfig))

    return camera

def startSwitchedCamera(config):
    """Start running the switched camera."""
    print("Starting switched camera '{}' on {}".format(config.name, config.key))
    server = CameraServer.getInstance().addSwitchedCamera(config.name)

    def listener(fromobj, key, value, isNew):
        if isinstance(value, float):
            i = int(value)
            if i >= 0 and i < len(cameras):
              server.setSource(cameras[i])
        elif isinstance(value, str):
            for i in range(len(cameraConfigs)):
                if value == cameraConfigs[i].name:
                    server.setSource(cameras[i])
                    break
    NetworkTablesInstance.getDefault().getEntry(config.key).addListener(
listener,
NetworkTablesInstance.NotifyFlags.IMMEDIATE |
NetworkTablesInstance.NotifyFlags.NEW |
NetworkTablesInstance.NotifyFlags.UPDATE)
    return server
    
def visionprocces_yellow():
        cv2.namedWindow("Yellow_Vision", cv2.WINDOW_AUTOSIZE)
        image = np.zeros(shape=(160, 120, 3), dtype=np.uint8)
        cs = CameraServer.getInstance()
        cvSink = cs.getVideo()
        thresholdStream = cs.putVideo("Yellow_Vision", 160,120)
        time.sleep(1)
        while True:
            print("Running")
        # Tell the CvSink to grab a frame from the camera and put it
        # in the source image.  If there is an error notify the output.
            time, image = cvSink.grabFrame(image)
            image = cv2.blur(image, (10,10))
            img_hsv=cv2.cvtColor(image,cv2.COLOR_BGR2HSV)
            img_threshold = cv2.inRange(img_hsv, 
                (lowh.getNumber(13.33), lows.getNumber(166.67), lowv.getNumber(173.33)), 
                (highh.getNumber(26.67), highs.getNumber(340), highv.getNumber(340))
        )
            img_contours = img_threshold.copy()
            contours, hierarchy = cv2.findContours(img_contours, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            area_cnt = cv2.contourArea(contours)
            for cnt in contours:
                if cv2.contourArea(area_cnt) < 50:
                    continue
                x,y,w,h = cv2.boundingRect(cnt)
                cv2.rectangle(image,(x,y),(x+w,y+h),(0,255,0),2)
                cv2.ellipse(image,(x/2,y/2),(10,10),0,0,360,(255,0,0),-1)
            thresholdStream.putFrame(img_threshold)

def visionprocces_green():
    cv2.namedWindow("Blue_Vision", cv2.WINDOW_AUTOSIZE)
    image = np.zeros(shape=(160, 120, 3), dtype=np.uint8)
    cs = CameraServer.getInstance()
    cvSink = cs.getVideo()
    thresholdStream = cs.putVideo("Blue_Vision", 160,120)
    time.sleep(1)
    while True:
        print("Running")
        # Tell the CvSink to grab a frame from the camera and put it
        # in the source image.  If there is an error notify the output.
        time, image = cvSink.grabFrame(image)
        image = cv2.blur(image, (10,10))
        img_hsv=cv2.cvtColor(image,cv2.COLOR_BGR2HSV)
        img_threshold = cv2.inRange(img_hsv, 
            (lowh.getNumber(13.33), lows.getNumber(166.67), lowv.getNumber(173.33)), 
            (highh.getNumber(26.67), highs.getNumber(340), highv.getNumber(340))
        )
        img_contours = img_threshold.copy()
        contours, hierarchy = cv2.findContours(img_contours, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        area_cnt = cv2.contourArea(cnt)
        for cnt in contours:
            if cv2.contourArea(area_cnt) < 50:
                continue
            x,y,w,h = cv2.boundingRect(cnt)
            cv2.cv2Color(area_cnt,cv2.COLOR_HSV2BGR)
            cv2.rectangle(image,(x,y),(x+w,y+h),(0,255,0),2)
            cv2.ellipse(image,(x/2,y/2),(10,10),0,0,360,(255,0,0),-1)
        thresholdStream.putFrame(img_threshold)

    
if __name__ == "__main__":
    if len(sys.argv) >= 2:
        configFile = sys.argv[1]

    # read configuration
    if not readConfig():
        sys.exit(1)

    # start NetworkTables
    ntinst = NetworkTablesInstance.getDefault()
    if server:
        print("Setting up NetworkTables server")
        ntinst.startServer()
    else:
        print("Setting up NetworkTables client for team {}".format(team))
        ntinst.startClientTeam(team)
        ntinst.startDSClient()

    # start cameras
    for config in cameraConfigs:
        cameras.append(startCamera(config))

    # start switched cameras
    for config in switchedCameraConfigs:
        startSwitchedCamera(config)

    while True:
        visionprocces_yellow() 
