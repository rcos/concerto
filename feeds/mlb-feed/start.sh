#!/bin/bash

. .venv/bin/activate
fastapi run --host 0.0.0.0 --port 43679
deactivate