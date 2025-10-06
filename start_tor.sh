#!/usr/bin/env bash
set -e

sudo systemctl start tor
sudo systemctl enable tor
sudo systemctl status tor
