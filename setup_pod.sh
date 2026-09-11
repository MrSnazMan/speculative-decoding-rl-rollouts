#!/bin/bash
# Combined pod setup: launches vLLM pull+server (Track A) and terminal-bench/uv/Python3.12
# install (Track B) as truly parallel background jobs from one SSH call.
#
# IMPORTANT: run `sudo usermod -aG docker ubuntu` in a PRIOR, SEPARATE ssh call first,
# then reconnect (fresh SSH session) before running this script — group membership
# changes don't apply within the same shell session that ran usermod (bit us in Pod F).
#
# Usage: setup_pod.sh <mtp_speculative_config_json_or_empty>
#   e.g. setup_pod.sh ''                                                        (MTP off)
#        setup_pod.sh '{"method":"mtp","num_speculative_tokens":3}'             (MTP on)
set -e
SPEC_CONFIG="$1"

mkdir -p /home/ubuntu/hfcache /home/ubuntu/tbrun/prompt-templates

SPEC_ARGS=""
if [ -n "$SPEC_CONFIG" ]; then
  SPEC_ARGS="--speculative-config $SPEC_CONFIG"
fi

# --- Track A: vLLM pull + server launch (background, long pole) ---
nohup bash -c "
docker pull vllm/vllm-openai:v0.29.0 && \
docker run -d --gpus all \
  -e HF_HUB_ENABLE_HF_TRANSFER=0 \
  --shm-size=16g \
  -v /home/ubuntu/hfcache:/root/.cache/huggingface \
  -p 8000:8000 \
  --name vllm_server \
  vllm/vllm-openai:v0.29.0 \
  --model Qwen/Qwen3.8-27B-FP8 \
  --enforce-eager \
  --max-model-len 4096 \
  --gpu-memory-utilization 0.85 \
  --kv-cache-dtype fp8_e4m3 \
  --trust-remote-code \
  --port 8000 \
  $SPEC_ARGS
" > /home/ubuntu/vllm_track.log 2>&1 &
echo "VLLM_TRACK_PID:$!"

# --- Track B: uv + Python 3.12 + terminal-bench + gepa (background, in parallel) ---
nohup bash -c '
curl -LsSf https://astral.sh/uv/install.sh | sh
export PATH=$HOME/.local/bin:$PATH
cd /home/ubuntu/tbrun
uv venv --python 3.12 .venv
uv pip install --python .venv terminal-bench "gepa[full]" litellm pydantic
' > /home/ubuntu/tb_track.log 2>&1 &
echo "TB_TRACK_PID:$!"

echo "BOTH_TRACKS_LAUNCHED"
