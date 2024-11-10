#!/bin/zsh

source ~/.zshrc
cd /Volumes/Data/AI/MyNLP/RAG
conda activate chatgpt
uvicorn api:app --port 8000
