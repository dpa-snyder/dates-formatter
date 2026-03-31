#!/bin/zsh

if [[ -x ".venv/bin/python" ]]; then
  ./.venv/bin/python -W ignore::DeprecationWarning -m unittest discover -s tests -q
else
  python3 -W ignore::DeprecationWarning -m unittest discover -s tests -q
fi
