#!/bin/bash

# Run the application on port 5003
gunicorn --bind 0.0.0.0:5003 --reuse-port --reload main:app