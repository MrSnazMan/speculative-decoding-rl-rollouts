#!/bin/bash
# usage: launch_vllm_dspark.sh [num_speculative_tokens]  (default 7)
set -e
NST="${1:-7}"
docker rm -f vllm_server 2>/dev/null || true
docker run -d --gpus all -e HF_HUB_ENABLE_HF_TRANSFER=0 --shm-size=16g \
  -v /home/ubuntu/hfcache:/root/.cache/huggingface -p 8000:8000 \
  --name vllm_server --restart no vllm/vllm-openai:v0.29.0 \
  --model Qwen/Qwen3.8-27B-FP8 --enforce-eager --max-model-len 32768 \
  --gpu-memory-utilization 0.85 --kv-cache-dtype fp8_e4m3 --trust-remote-code --port 8000 \
  --speculative-config "{\"method\": \"dspark\", \"model\": \"RadixArk/Qwen3.8-27B-DSpark\", \"num_speculative_tokens\": $NST}"
