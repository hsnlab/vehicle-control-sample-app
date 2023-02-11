import datetime
import greengrasssdk
import json
import socket
import time
from ast import literal_eval

from json import dumps

import random

# Globals ############################################################

GLOBALS_SET = False

TEST_MODE = False
THRESHOLD = 0.01
USE_INFERENCE_WITH_HIGHEST_CONFIDENCE = True
STOP_LABELS = ['prohibitory', 'mandatory', 'danger']
UP_COMMAND = b'SDR\xfe\x7f\x00\x80\x00~\x00\x00\x02{'
STOP_COMMAND = b'SDR\x7f\x7f\x00\x7f\x00\x7f\x00\x00\x01\xfc'

s = None
VEHICLE_IP = None

def init_globals(context):
    global GLOBALS_SET
    if not GLOBALS_SET:
        GLOBALS_SET = True

        global THRESHOLD
        global USE_INFERENCE_WITH_HIGHEST_CONFIDENCE
        global STOP_LABELS
        global UP_COMMAND
        global STOP_COMMAND
        
        if hasattr(context.env_vars, 'THRESHOLD'):
            THRESHOLD = float(context.env_vars.THRESHOLD)
        if hasattr(context.env_vars, 'USE_INFERENCE_WITH_HIGHEST_CONFIDENCE'):
            USE_INFERENCE_WITH_HIGHEST_CONFIDENCE = bool(
                context.env_vars.USE_INFERENCE_WITH_HIGHEST_CONFIDENCE)
        if hasattr(context.env_vars, 'STOP_LABELS'):
            STOP_LABELS = literal_eval(context.env_vars.STOP_LABELS)
        if hasattr(context.env_vars, 'UP_COMMAND'):
            UP_COMMAND = bytes(context.env_vars.UP_COMMAND)
        if hasattr(context.env_vars, 'STOP_COMMAND'):
            STOP_COMMAND = bytes(context.env_vars.STOP_COMMAND)

def init_globals_and_warmup(event, context):
    init_globals(context)
    if event == context.warmup_event:
        time.sleep(context.warmup_wait_delay)
        return True
        
# User code ##########################################################

def send_to_vehicle(socket, control_msg):
    if control_msg.get('human-readable') == 'Up':
        if not TEST_MODE:
            socket.send(UP_COMMAND)
    elif control_msg.get('human-readable') == 'Stop':
        if not TEST_MODE:
            socket.send(STOP_COMMAND)

def send(socket, control_msg):
    send_to_vehicle(socket, control_msg)

def control(event, context):
    global VEHICLE_IP
    global s
    global TEST_MODE

    vehicle_inferences = context.var.INFERENCES.get(event["id"])
    if not vehicle_inferences:
        return
    inference_read = time.time()
    if vehicle_inferences:
        vehicle_inferences = json.loads(vehicle_inferences)
    else:
        print("Nothing found in datastore")
        return
    
    vehicle_ip = vehicle_inferences["control"]["ip"]
    vehicle_port = vehicle_inferences["control"]["port"]
    TEST_MODE = not vehicle_inferences["control"]["enabled"]
    inferences = vehicle_inferences["inference"]

    if vehicle_ip != VEHICLE_IP and not TEST_MODE:
        VEHICLE_IP = vehicle_ip
        if s != None:
            s.close()
            s = None
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((vehicle_ip, vehicle_port))
    
    msg = {'timestamp': str(datetime.datetime.now()),
           'vehicle-ip': vehicle_ip,
           'vehicle-port': vehicle_port,
           'label': "No stop condition detected",
           'human-readable': "Up"}
    
    if inferences:
        ics = [(i.get('confidence'), i.get('label')) for i in inferences if i and len(i) > 0 and i.get('label') and (i.get('label') in STOP_LABELS)]
        if ics:
            confidences = [c[0] for c in ics]
            max_confidence = max(confidences)

            msg['threshold'] = THRESHOLD
            msg['label'] = "label: %s; confidence: %s; threshold: %s" % (ics[confidences.index(max_confidence)][1], max_confidence, THRESHOLD)
            msg['confidence'] = max_confidence
            if max_confidence > THRESHOLD:
                msg['human-readable'] = "Stop"
            
    if not inferences:
        msg['label'] = "No object detected"
    send(s, msg)

# Handler ############################################################        
        
def handler(event, context):
    warmup_call = init_globals_and_warmup(event, context)
    
    if warmup_call:
        # No need to do anything.
        return
               
    # Call user function entry point.
    control(event, context)
    # Emulate communication latency with vehicle:
    # time.sleep((5 + random.randint(0, 1)) / 1000)
