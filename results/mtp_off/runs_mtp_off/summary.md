# MTP Comparison - mtp_off (rebuilt from raw tb tree)

**Model**: openai/Qwen/Qwen3.8-27B-FP8  
**vLLM**: no --speculative-config; --enforce-eager --max-model-len 32768 --kv-cache-dtype fp8_e4m3 --gpu-memory-utilization 0.85  
**Tasks**: 50  **Resolved**: 21 (42.0%)  
**Eval wall clock**: 3095s (51.6 min), n_concurrent=8  
**Tokens**: 477,001 in / 36,392 out  
**Unresolved failure modes**: {'unset': 6, 'agent_timeout': 15, 'parse_error': 7, 'unknown_agent_error': 1}  

> Rebuilt from raw tb results.json; run_condition.py was killed before it wrote its own summary (post-eval orphaned-agent retry loop hung the tb process). Eval itself completed cleanly.

| Task | Resolved | Agent s | Trial s | In tok | Out tok | Failure mode |
|---|:--:|--:|--:|--:|--:|---|
| crack-7z-hash.hard | ✅ | 527 | 758 | 0 | 0 |  |
| git-workflow-hack | ✅ | 649 | 680 | 0 | 0 |  |
| simple-sheets-put | ✅ | 493 | 529 | 0 | 0 |  |
| solana-data | ✅ | 660 | 692 | 0 | 0 |  |
| sqlite-db-truncate | ✅ | 491 | 526 | 0 | 0 |  |
| crack-7z-hash | ✅ | 181 | 212 | 76135 | 2216 |  |
| crack-7z-hash.easy | ✅ | 112 | 371 | 24731 | 1211 |  |
| create-bucket | ✅ | 169 | 195 | 22525 | 1880 |  |
| csv-to-parquet | ✅ | 240 | 273 | 24615 | 1261 |  |
| extract-safely | ✅ | 43 | 127 | 6273 | 601 |  |
| fibonacci-server | ✅ | 109 | 143 | 9184 | 1549 |  |
| fix-pandas-version | ✅ | 187 | 250 | 20417 | 1696 |  |
| fix-permissions | ✅ | 37 | 73 | 3724 | 495 |  |
| heterogeneous-dates | ✅ | 109 | 163 | 7535 | 1318 |  |
| modernize-fortran-build | ✅ | 148 | 212 | 28401 | 2145 |  |
| openssl-selfsigned-cert | ✅ | 200 | 236 | 15068 | 2916 |  |
| organization-json-generator | ✅ | 223 | 258 | 55595 | 3310 |  |
| processing-pipeline | ✅ | 187 | 232 | 33061 | 2595 |  |
| prove-plus-comm | ✅ | 49 | 84 | 6567 | 683 |  |
| sqlite-with-gcov | ✅ | 235 | 265 | 53661 | 2590 |  |
| swe-bench-langcodes | ✅ | 82 | 178 | 8806 | 1013 |  |
| build-tcc-qemu | ❌ | 660 | 939 | 0 | 0 | agent_timeout |
| cartpole-rl-training | ❌ | 660 | 686 | 0 | 0 | agent_timeout |
| extract-moves-from-video | ❌ | 660 | 691 | 0 | 0 | agent_timeout |
| gpt2-codegolf | ❌ | 660 | 730 | 0 | 0 | agent_timeout |
| jupyter-notebook-server | ❌ | 366 | 408 | 0 | 0 | agent_timeout |
| path-tracing | ❌ | 511 | 539 | 0 | 0 | agent_timeout |
| path-tracing-reverse | ❌ | 552 | 640 | 0 | 0 | agent_timeout |
| polyglot-c-py | ❌ | 660 | 719 | 0 | 0 | agent_timeout |
| polyglot-rust-c | ❌ | 660 | 723 | 0 | 0 | agent_timeout |
| raman-fitting | ❌ | 660 | 691 | 0 | 0 | agent_timeout |
| raman-fitting.easy | ❌ | 660 | 691 | 0 | 0 | agent_timeout |
| reshard-c4-data | ❌ | 660 | 770 | 0 | 0 | agent_timeout |
| sanitize-git-repo.hard | ❌ | 647 | 673 | 0 | 0 | agent_timeout |
| security-vulhub-minio | ❌ | 660 | 694 | 0 | 0 | agent_timeout |
| write-compressor | ❌ | 660 | 692 | 0 | 0 | agent_timeout |
| build-initramfs-qemu | ❌ | 660 | 741 | 0 | 0 | parse_error |
| chess-best-move | ❌ | 660 | 741 | 0 | 0 | parse_error |
| configure-git-webserver | ❌ | 660 | 717 | 0 | 0 | parse_error |
| get-bitcoin-nodes | ❌ | 660 | 684 | 0 | 0 | parse_error |
| intrusion-detection | ❌ | 660 | 695 | 0 | 0 | parse_error |
| password-recovery | ❌ | 660 | 708 | 0 | 0 | parse_error |
| tmux-advanced-workflow | ❌ | 660 | 718 | 0 | 0 | parse_error |
| sanitize-git-repo | ❌ | 294 | 325 | None | None | unknown_agent_error |
| decommissioning-service-with-sensitive-data | ❌ | 92 | 133 | 19423 | 1308 | unset |
| fix-git | ❌ | 133 | 167 | 18482 | 1635 | unset |
| hf-model-inference | ❌ | 274 | 301 | 27729 | 2709 | unset |
| new-encrypt-command | ❌ | 155 | 192 | 13029 | 2246 | unset |
| nginx-request-logging | ❌ | 41 | 74 | 1064 | 514 | unset |
| vim-terminal-task | ❌ | 35 | 73 | 976 | 501 | unset |