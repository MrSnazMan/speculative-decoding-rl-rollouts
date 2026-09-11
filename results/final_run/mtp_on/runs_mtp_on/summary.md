# MTP Comparison — mtp_on

**Model**: openai/Qwen/Qwen3.8-27B-FP8  
**Run status**: ok  
**Tasks x attempts**: 50 x 3 = 150 trials  
**Resolved trials**: 71/150  **mean accuracy**: 47.3%  
**Tasks solved on >=1 attempt (pass@3)**: 29/50 (58.0%)  
**tb-reported accuracy**: 0.47333333333333333  
**Wall clock**: 4263s (71.0 min)  
**Generated tokens**: 800962.0  **tok/s**: 187.9  
**Draft acceptance**: 86.8% (578723/666617)  

| Task | resolved/3 | rate | pass@3 | failure modes |
|---|:--:|:--:|:--:|---|
| fix-permissions | 3/3 | 100% | Y | - |
| crack-7z-hash | 3/3 | 100% | Y | - |
| password-recovery | 1/3 | 33% | Y | unknown_agent_error |
| sqlite-with-gcov | 3/3 | 100% | Y | - |
| polyglot-rust-c | 0/3 | 0% | N | unknown_agent_error |
| path-tracing | 1/3 | 33% | Y | unknown_agent_error |
| get-bitcoin-nodes | 1/3 | 33% | Y | fatal_llm_parse_error |
| intrusion-detection | 0/3 | 0% | N | unset |
| write-compressor | 0/3 | 0% | N | agent_timeout, unknown_agent_error |
| solana-data | 0/3 | 0% | N | unknown_agent_error, unset |
| crack-7z-hash.easy | 3/3 | 100% | Y | - |
| raman-fitting.easy | 0/3 | 0% | N | agent_timeout, unknown_agent_error, unset |
| tmux-advanced-workflow | 3/3 | 100% | Y | - |
| raman-fitting | 0/3 | 0% | N | unknown_agent_error, unset |
| polyglot-c-py | 0/3 | 0% | N | agent_timeout, unknown_agent_error |
| cartpole-rl-training | 0/3 | 0% | N | agent_timeout, parse_error |
| path-tracing-reverse | 0/3 | 0% | N | unknown_agent_error |
| sanitize-git-repo | 3/3 | 100% | Y | - |
| create-bucket | 3/3 | 100% | Y | - |
| openssl-selfsigned-cert | 3/3 | 100% | Y | - |
| heterogeneous-dates | 3/3 | 100% | Y | - |
| crack-7z-hash.hard | 2/3 | 67% | Y | unset |
| build-tcc-qemu | 2/3 | 67% | Y | unknown_agent_error |
| fibonacci-server | 1/3 | 33% | Y | unset |
| jupyter-notebook-server | 0/3 | 0% | N | unset |
| extract-moves-from-video | 0/3 | 0% | N | agent_timeout, parse_error |
| nginx-request-logging | 0/3 | 0% | N | unset |
| csv-to-parquet | 3/3 | 100% | Y | - |
| fix-git | 2/3 | 67% | Y | unset |
| prove-plus-comm | 3/3 | 100% | Y | - |
| security-vulhub-minio | 0/3 | 0% | N | unknown_agent_error |
| chess-best-move | 0/3 | 0% | N | agent_timeout, unknown_agent_error, unset |
| swe-bench-langcodes | 3/3 | 100% | Y | - |
| fix-pandas-version | 3/3 | 100% | Y | - |
| reshard-c4-data | 0/3 | 0% | N | unset |
| modernize-fortran-build | 3/3 | 100% | Y | - |
| decommissioning-service-with-sensitive-data | 0/3 | 0% | N | unset |
| simple-sheets-put | 3/3 | 100% | Y | - |
| processing-pipeline | 3/3 | 100% | Y | - |
| gpt2-codegolf | 0/3 | 0% | N | fatal_llm_parse_error, unknown_agent_error |
| sqlite-db-truncate | 2/3 | 67% | Y | unset |
| build-initramfs-qemu | 0/3 | 0% | N | test_timeout |
| hf-model-inference | 0/3 | 0% | N | unset |
| new-encrypt-command | 2/3 | 67% | Y | unset |
| organization-json-generator | 1/3 | 33% | Y | unset |
| configure-git-webserver | 0/3 | 0% | N | unset |
| sanitize-git-repo.hard | 3/3 | 100% | Y | - |
| git-workflow-hack | 2/3 | 67% | Y | unknown_agent_error |
| extract-safely | 3/3 | 100% | Y | - |
| vim-terminal-task | 0/3 | 0% | N | unset |