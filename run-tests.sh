#!/bin/zsh

python3 -W ignore::DeprecationWarning -m unittest discover -s tests -q
