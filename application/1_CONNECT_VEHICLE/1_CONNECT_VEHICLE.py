import json
import time

# Globals ############################################################
GLOBALS_SET = False
AWAITING_INIT = True

CALL_COUNTER = 1

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
        time.sleep(context.warmup_wait_delay)
        return True

# User code ##########################################################

def process_vehicles(event, context):
    
    if context.env_vars.VEHICLES != "":
        for vehicle in json.loads(context.env_vars.VEHICLES):
            global CALL_COUNTER
            vehicle.update({"call": {"counter": CALL_COUNTER,
                                     "start": time.time()}})
            context.downstream_functions.2_GRAB_IMAGE.call(
                vehicle, context)
            CALL_COUNTER += 1
            
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
    process_vehicles(event, context)

    
