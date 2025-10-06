#!/usr/bin/env bash
set -e

sudo systemctl restart tor
sudo systemctl status tor
