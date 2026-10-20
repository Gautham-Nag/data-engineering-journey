#!/bin/bash
# Run after every workspace restart: reinstalls packages and reapplies the RAGAS 0.4.3 fix.
pip install -q -r requirements.txt
BASE=/opt/venv/lib/python3.10/site-packages/ragas/llms/base.py
sed -i 's/from langchain_community.chat_models.vertexai import ChatVertexAI/from langchain_google_vertexai import ChatVertexAI/' "$BASE"
sed -i 's/from langchain_community.llms import VertexAI/from langchain_google_vertexai import VertexAI/' "$BASE"
python -W ignore -c "import ragas; print('RAGAS OK:', ragas.__version__)"