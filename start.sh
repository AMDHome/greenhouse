#!/bin/bash
screen -dmS gh (python3 main.py | tee stdout.log) 3>&1 1>&2 2>&3 | tee stderr.log
