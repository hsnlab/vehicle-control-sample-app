import datetime
import json
import time

from time import sleep

# Globals ############################################################

GLOBALS_SET = False

DELAY = 0.05
INIT_DELAY = 8
AWAITING_INIT = True

def init_globals(context):
    global GLOBALS_SET
    if not GLOBALS_SET:
        GLOBALS_SET = True

        global DELAY
        global INIT_DELAY

        if hasattr(context.env_vars, 'DELAY'):
            DELAY = float(context.env_vars.DELAY)
        if hasattr(context.env_vars, 'INIT_DELAY'):
            INIT_DELAY = float(context.env_vars.INIT_DELAY)

def init_globals_and_warmup(event, context):
    init_globals(context)
    if event == context.warmup_event:
        sleep(context.warmup_wait_delay)
        return True
            
# User code ##########################################################

def control_all(event, context):

    if context.env_vars.VEHICLES != "":
        for vehicle in json.loads(context.env_vars.VEHICLES):
            context.downstream_functions.5_COTNROL_ONE_VEHICLE.call(
                {"id": vehicle["id"]}, context)
            
    time.sleep(DELAY)

# Handler ############################################################
            
def handler(event, context):
    warmup_call = init_globals_and_warmup(event, context)
    
    if warmup_call:
        # Do special setup when receiving a warmup call.
        return

    global AWAITING_INIT
    global INIT_DELAY
    if AWAITING_INIT:
        time.sleep(INIT_DELAY)
        AWAITING_INIT = False
    # Call user function entry point.
    control_all(event, context)
