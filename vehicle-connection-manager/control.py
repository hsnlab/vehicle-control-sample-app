#!/usr/bin/env python3.8

import argparse
import json
import requests
import time

api = {"offload": "change-downstream-function-invocations-to-lambda",
       "env": "set-env-var"}

nodes = ["E0", "Ew", "Eb"]

with open("../vehiclep4offload.template", "r") as f:
    template = json.load(f)

functions = ["01CONNECTVEHICLEE0", "04CONTROLALLVEHICLESE0"]
ports = {}
for func in functions:
    ports[func] = template["Resources"][func]["Properties"]["Environment"]["Variables"]["AWS_ADAPTER_CONFIG_PORT"]

def send_cmd(ip, port, api, json_cmd, print_cmd, send):
    url = f'http://{ip}:{port}/config/{api}'
    if print_cmd:
        print(f"curl -d '{json.dumps(json_cmd)}' -H 'Content-Type: application/json' -X POST {url}")
    if send_cmd:
        r = requests.post(url, json=json_cmd)
        print(f"Return code: {r.status_code}")
        print(f"Return message: {r.json()}")
    
def main():
    parser = argparse.ArgumentParser(description='')
    parser.add_argument('ip', nargs='?', metavar='ip',
                        help='')
    parser.add_argument("-d", "--display",
                        help="",
                        action="store_true")
    parser.add_argument("-s", "--send",
                        help="",
                        action="store_true")
    parser.add_argument("-1", "--init",
                        help="",
                        action="store_true")
    parser.add_argument("-2", "--start",
                        help="",
                        action="store_true")
    parser.add_argument("-3", "--offload",
                        help="",
                        action="store_true")
    parser.add_argument("-4", "--revert",
                        help="",
                        action="store_true")
    parser.add_argument("-5", "--stop",
                        help="",
                        action="store_true")
    args = parser.parse_args()

    ip = "localhost"

    if args.ip:
        ip = args.ip

    print_cmd = False
    if args.display:
         print_cmd = True

    send = False
    if args.send:
         send = True
        
    if args.init:
        print("init")
        # Set function `3_INFER' to run on node `Ew'.
        send_cmd(ip,
                 ports[functions[0]],
                 api["offload"],
                 {"reconfiguration": {"2_GRAB_IMAGE": {"3_INFER": nodes[1]}}},
                 print_cmd, send)
    elif args.start:
        print("start")
        # Connect one vehicle.
        # Set vehicle for function `1_CONNECT_VEHICLE'.
        send_cmd(ip,
                 ports[functions[0]],
                 api["env"],
                 {"reconfiguration":
                  {"1_CONNECT_VEHICLE":
                   {"VEHICLES":
                    "[{\"id\": \"1\", \"video\": {\"enabled\": true, \"ip\": \"192.168.10.200\"}, \"control\": {\"enabled\": true, \"ip\": \"192.168.10.160\", \"port\": 5050}}]"}}},
                 print_cmd, send)
        time.sleep(10)

        # Set vehicle for function `4_CONTROL_ALL_VEHICLES'.
        send_cmd(ip,
                 ports[functions[1]],
                 api["env"],
                 {"reconfiguration": {"4_CONTROL_ALL_VEHICLES": {"VEHICLES": "[{\"id\": \"1\"}]"}}},
                 print_cmd, send)

    # Only for evaluating warm-up performance.
    elif args.offload:
        print("offload")
        # Set function `3_INFER' to run on node `Eb'.
        send_cmd(ip,
                 ports[functions[0]],
                 api["offload"],
                 {"reconfiguration": {"2_GRAB_IMAGE": {"3_INFER": nodes[2]}}},
                 print_cmd, send)
    # Only for testing purposes.
    elif args.revert:
        print("revert")
        # Set function `3_INFER' to run on node `Ew'.
        send_cmd(ip,
                 ports[functions[0]],
                 api["offload"],
                 {"reconfiguration": {"2_GRAB_IMAGE": {"3_INFER": nodes[1]}}},
                 print_cmd, send)
    elif args.stop:
        print("stop")
        # Connect all vehicles.
        # Remove every vehicles for function `4_CONTROL_ALL_VEHICLES'.
        send_cmd(ip,
                 ports[functions[1]],
                 api["env"],
                 {"reconfiguration": {"4_CONTROL_ALL_VEHICLES": {"VEHICLES": ""}}},
                 print_cmd, send)
        # Remove every vehicles for function `1_CONNECT_VEHICLE'.
        send_cmd(ip,
                 ports[functions[0]],
                 api["env"],
                 {"reconfiguration": {"1_CONNECT_VEHICLE": {"VEHICLES": ""}}},
                 print_cmd, send)


if __name__ == '__main__':
    main()
