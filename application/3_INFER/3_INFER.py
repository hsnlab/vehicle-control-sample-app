import base64
import cv2
import json
import numpy as np
import os
import traceback

import time

import socket
from json import dumps

# Globals ############################################################
import random
import string
instance_id = ''.join(random.sample(string.ascii_lowercase, 8))

GLOBALS_SET = False

net = None

INFER_START = None

def init_globals(context):
    global GLOBALS_SET
    if not GLOBALS_SET:
        GLOBALS_SET = True

        global CLASSES
        global net

        # Initialize the list of class labels MobileNet SSD was trained to detect
        CLASSES = ["background", "aeroplane", "bicycle", "bird", "boat",
	"bottle", "bus", "car", "cat", "chair", "cow", "diningtable",
	"dog", "horse", "motorbike", "person", "pottedplant", "sheep",
	"sofa", "train", "tvmonitor"]

        # Load serialized model from disk
        net = cv2.dnn.readNetFromCaffe(
            "3_INFER/ml_artifacts/MobileNetSSD_deploy.prototxt.txt",
            "3_INFER/ml_artifacts/MobileNetSSD_deploy.caffemodel")

def init_globals_and_warmup(event, context):
    init_globals(context)
    if event == context.warmup_event:
        time.sleep(context.warmup_wait_delay)
        return True

# User code ##########################################################

def detect_objects(image):
    (h, w) = image.shape[:2]
    blob = cv2.dnn.blobFromImage(image, 0.007843, (h, w), 127.5)
    
    net.setInput(blob)
    detections = net.forward()

    labels = []
    for i in np.arange(0, detections.shape[2]):
        confidence = detections[0, 0, i, 2]
        if confidence > 0:
            labels.insert(
                0, {"label": CLASSES[int(detections[0, 0, i, 1])],
                    "confidence": float(confidence)})

    return labels

def infer(event, context):    
    key = event["id"]
    image = event["img"]

    s = time.time()
    image = base64.b64decode(image)
    image = np.frombuffer(image, dtype=np.uint8);
    image = cv2.imdecode(image, flags=1)
    
    s = time.time()
    labels = detect_objects(image)

    s = time.time()
    inf = []
    for l in labels:
        new_l = {}
        for key, value in l.items():
            if type(value) == np.float32:
                new_l[key] = float(value)
            else:
                new_l[key] = value
        inf.append(new_l)

    vehicle_id = event.pop("id")
    event.pop("img")
    event["inference"] = inf

    context.var.INFERENCES.set(vehicle_id, json.dumps(event))
        
# Handler ############################################################

def handler(event, context):
    warmup_call = init_globals_and_warmup(event, context)
    
    if warmup_call:
        # No need to do anything.
        return
    
    global INFER_START
    INFER_START = time.time()
    # Call user function entry point.
    infer(event, context)
