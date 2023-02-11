import base64
import cv2
import time

from os import listdir
from os.path import isfile
from os.path import join as os_join
from time import sleep

# Globals ############################################################
import random
import string
instance_id = ''.join(random.sample(string.ascii_lowercase, 8))

GLOBALS_SET = False

ANNOTATIONS_LIST = []
TARGET_VIDEO_SOURCE = None
TARGET_VIDEO_SOURCE_URL = ""


def init_globals(context):
    global GLOBALS_SET
    if not GLOBALS_SET:        
        GLOBALS_SET = True

        global SCALE_PERCENT
        global TEST_FILES
        global TEST_DELAY_S
        global TEST_JITTER_MS

        SCALE_PERCENT = False
        if hasattr(context.env_vars, 'SCALE_PERCENT'):
            SCALE_PERCENT = float(context.env_vars.SCALE_PERCENT)

        TEST_DELAY_S = 0
        if hasattr(context.env_vars, 'TEST_DELAY_MS'):
            TEST_DELAY_S = float(context.env_vars.TEST_DELAY_MS) / 1000

        TEST_JITTER_MS = 0
        if hasattr(context.env_vars, 'TEST_JITTER_MS'):
            TEST_JITTER_MS = float(context.env_vars.TEST_JITTER_MS)

        test_files_path = "2_GRAB_IMAGE/img_sample/"
        TEST_FILES = [os_join(test_files_path, f) for f in listdir(test_files_path) if isfile(os_join(test_files_path, f))]

def init_globals_and_warmup(event, context):
    init_globals(context)
    if event == context.warmup_event:
        sleep(context.warmup_wait_delay)
        return True

# User code ##########################################################

def get_test_file():
    global TEST_FILES
    return random.choice(TEST_FILES)

def preprocess_and_encode_image(original, scale_percent, grayscale):
    # Resize picture.
    preprocessed = original
    if scale_percent:
        (h, w) = original.shape[:2]
        width = int(original.shape[1] * scale_percent / 100.0)
        height = int(original.shape[0] * scale_percent / 100.0)
        dim = (width, height)
        preprocessed = cv2.resize(original, dim, interpolation=cv2.INTER_AREA)
        
    # Grayscale picture.
    if grayscale:
        preprocessed = cv2.cvtColor(preprocessed, cv2.COLOR_BGR2GRAY)
    
    s = time.time()
    retval, buffer = cv2.imencode('.jpg', preprocessed)
    encoded = base64.b64encode(buffer).decode("utf-8")
    return encoded

def get_camera_img(source, scale_percent, grayscale):
    img = None
    if source:
        if source.isOpened():
            s = time.time()
            # Try to empty read buffer and store the most up-to-date image.
            while(True):
                prev_time=time.time()
                ref = source.grab()
                if (time.time()-prev_time)>0.030: # around 33 FPS
                    break

            # Read the frame properly and process it.
            e = time.time()
            ret, frame = source.read()
            if ret:
                try:
                    # Test if a valid picture was read.
                    value = frame[0][0][0]
                    img = preprocess_and_encode_image(image, scale_percent, grayscale)

                except Exception as e:
                    print(f"Exception while trying to read data from video frame:\n{e}")

        else:
            print("Video source is not open")
    else:
        print("Video source is empty")

    return img

def process_frame(source, event, context, scale_percent, grayscale):
    try:
        img = None
        if event["video"]["enabled"]:
            img = get_camera_img(source, scale_percent, grayscale)
        else: # Test call.
            img = get_test_file()
            img = preprocess_and_encode_image(cv2.imread(img), scale_percent, grayscale)

        if img is not None:
            event.pop("video")
            event["img"] = img
            context.downstream_functions.3_INFER.call(event, context)
        else:
            print("No call for downstream function: image is empty")

        return True
    except Exception as e:
        print(f"instance {instance_id}: exception during image load: {e}")
        return False

def grab_image(event, context):
    global TARGET_VIDEO_SOURCE
    global SCALE_PERCENT

    if event:
        video = event.get("video")
        video_source_url = 'rtsp://root:password1@' + video["ip"] + '/live.sdp'
        
        global TARGET_VIDEO_SOURCE_URL
        if video["enabled"]:
            if TARGET_VIDEO_SOURCE_URL != video_source_url:
                TARGET_VIDEO_SOURCE_URL = video_source_url
                if TARGET_VIDEO_SOURCE:
                    try:
                        TARGET_VIDEO_SOURCE.release()
                    except Exception:
                        print("Could not release video source")
                        pass
                s = time.time()
                TARGET_VIDEO_SOURCE = cv2.VideoCapture(TARGET_VIDEO_SOURCE_URL)

        grayscale = False
        if SCALE_PERCENT:
            grayscale = True

        process_frame(TARGET_VIDEO_SOURCE,
                      event,
                      context,
                      SCALE_PERCENT,
                      grayscale)
    
# Handler ############################################################

def handler(event, context):
    warmup_call = init_globals_and_warmup(event, context)
    
    if warmup_call:
        # No need to do anything.
        return
               
    # Call user function entry point.
    sleep(TEST_DELAY_S + random.randint(0, TEST_JITTER_MS) / 1000)
    grab_image(event, context)
