#!/bin/bash

# Get the path of the current script
SCRIPT_PATH=$(dirname $(realpath $0))

# Create the systemd service file
echo "[Unit]
Description=pdfex
After=network.target

[Service]
Environment=\"VIRTUAL_ENV=$SCRIPT_PATH/env\"
Environment=\"PATH=$SCRIPT_PATH/env/bin:$PATH\"
ExecStart=$SCRIPT_PATH/env/bin/python $SCRIPT_PATH/extract.py
WorkingDirectory=$SCRIPT_PATH
Restart=always

[Install]
WantedBy=multi-user.target" | sudo tee /etc/systemd/system/pdfex.service

# Reload the systemd manager configuration
sudo systemctl daemon-reload

# Enable the service to start on boot
sudo systemctl enable pdfex

# Start the service
sudo systemctl start pdfex