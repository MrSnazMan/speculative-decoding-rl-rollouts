# MTP Comparison — mtp_off

**Model**: openai/Qwen/Qwen3.8-27B-FP8  
**Run status**: ok  
**Tasks x attempts**: 50 x 3 = 150 trials  
**Resolved trials**: 64/150  **mean accuracy**: 42.7%  
**Tasks solved on >=1 attempt (pass@3)**: 28/50 (56.0%)  
**tb-reported accuracy**: 0.4266666666666667  
**Wall clock**: 7936s (132.3 min)  
**Generated tokens**: 738047.0  **tok/s**: 93.0  
**Draft acceptance**: n/a (no speculation)  

| Task | resolved/3 | rate | pass@3 | failure modes |
|---|:--:|:--:|:--:|---|
| fix-permissions | 3/3 | 100% | Y | - |
| crack-7z-hash | 3/3 | 100% | Y | - |
| password-recovery | 1/3 | 33% | Y | agent_timeout |
| sqlite-with-gcov | 3/3 | 100% | Y | - |
| polyglot-rust-c | 0/3 | 0% | N | agent_timeout, parse_error |
| path-tracing | 1/3 | 33% | Y | agent_timeout |
| get-bitcoin-nodes | 0/3 | 0% | N | agent_timeout |
| intrusion-detection | 0/3 | 0% | N | unset |
| write-compressor | 0/3 | 0% | N | agent_timeout, parse_error |
| solana-data | 0/3 | 0% | N | agent_timeout, parse_error |
| crack-7z-hash.easy | 3/3 | 100% | Y | - |
| raman-fitting.easy | 0/3 | 0% | N | agent_timeout, unset |
| tmux-advanced-workflow | 3/3 | 100% | Y | - |
| raman-fitting | 0/3 | 0% | N | agent_timeout, unset |
| polyglot-c-py | 0/3 | 0% | N | agent_timeout |
| cartpole-rl-training | 0/3 | 0% | N | agent_timeout |
| path-tracing-reverse | 0/3 | 0% | N | agent_timeout |
| sanitize-git-repo | 2/3 | 67% | Y | agent_timeout |
| create-bucket | 3/3 | 100% | Y | - |
| openssl-selfsigned-cert | 2/3 | 67% | Y | unset |
| heterogeneous-dates | 3/3 | 100% | Y | - |
| crack-7z-hash.hard | 3/3 | 100% | Y | - |
| build-tcc-qemu | 1/3 | 33% | Y | agent_timeout, unknown_agent_error |
| fibonacci-server | 1/3 | 33% | Y | unset |
| jupyter-notebook-server | 0/3 | 0% | N | unset |
| extract-moves-from-video | 0/3 | 0% | N | agent_timeout |
| nginx-request-logging | 0/3 | 0% | N | unset |
| csv-to-parquet | 3/3 | 100% | Y | - |
| fix-git | 2/3 | 67% | Y | unset |
| prove-plus-comm | 3/3 | 100% | Y | - |
| security-vulhub-minio | 0/3 | 0% | N | agent_timeout, unknown_agent_error |
| chess-best-move | 0/3 | 0% | N | agent_timeout, parse_error |
| swe-bench-langcodes | 3/3 | 100% | Y | - |
| fix-pandas-version | 3/3 | 100% | Y | - |
| reshard-c4-data | 0/3 | 0% | N | unset |
| modernize-fortran-build | 3/3 | 100% | Y | - |
| decommissioning-service-with-sensitive-data | 0/3 | 0% | N | unset |
| simple-sheets-put | 3/3 | 100% | Y | - |
| processing-pipeline | 3/3 | 100% | Y | - |
| gpt2-codegolf | 0/3 | 0% | N | agent_timeout |
| sqlite-db-truncate | 1/3 | 33% | Y | agent_timeout |
| build-initramfs-qemu | 0/3 | 0% | N | parse_error, test_timeout |
| hf-model-inference | 0/3 | 0% | N | unset |
| new-encrypt-command | 1/3 | 33% | Y | unset |
| organization-json-generator | 1/3 | 33% | Y | unset |
| configure-git-webserver | 0/3 | 0% | N | agent_timeout, unset |
| sanitize-git-repo.hard | 2/3 | 67% | Y | unknown_agent_error |
| git-workflow-hack | 1/3 | 33% | Y | agent_timeout |
| extract-safely | 3/3 | 100% | Y | - |
| vim-terminal-task | 0/3 | 0% | N | unset |