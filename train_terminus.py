"""Terminus wrapper that applies Qwen3.8-27B's recommended *non-thinking / instruct*
sampling parameters to every litellm call, disables thinking mode, and caps
per-turn output length.

terminal-bench's Terminus forces strict structured (JSON schema) tool-call output,
which is an instruct pattern, so the non-thinking recommendation from the model
card applies:

    temperature=0.7, top_p=0.80, top_k=20, min_p=0.0,
    presence_penalty=1.5, repetition_penalty=1.0

Stock Terminus only ever passes `temperature` and `response_format` to
`litellm.completion` (verified in agent-logs/*/debug.json of the earlier runs),
leaving top_p at 1.0, top_k disabled, and no max_tokens -- off-spec for Qwen3,
which drove verbose runaway generation that ran to the context ceiling and
aborted agent runs. This threads the full set through properly.

`top_k`, `min_p`, `repetition_penalty` and `chat_template_kwargs` are vLLM
extensions, not OpenAI params -- and `LiteLLM.call()` hardcodes
`drop_params=True`, which would strip them if passed as plain kwargs -- so they go
via `extra_body`, which litellm forwards verbatim to the vLLM endpoint.
`temperature` (0.7), `top_p`, `presence_penalty` and `max_tokens` are standard
OpenAI params and pass as normal kwargs.

`max_tokens=2048` caps each turn. Stock `LiteLLM.call()` raises
`OutputLengthExceededError` on `finish_reason == "length"`, which (being in
Terminus's retry-exclusion list) would abort the whole task -- so we catch it
here and return the truncated text instead. If that text isn't valid JSON,
Terminus's own `ParseError` retry (up to 3x) handles it; the task no longer dies
on one over-long turn.
"""

from terminal_bench.agents.terminus_1 import Terminus
from terminal_bench.llms.base_llm import OutputLengthExceededError
from terminal_bench.llms.lite_llm import LiteLLM

# standard OpenAI params (safe as direct kwargs, not dropped by drop_params=True)
_OPENAI_SAMPLING = {
    "top_p": 0.80,
    "presence_penalty": 1.5,
    "max_tokens": 2048,
}
# vLLM-only params (must go via extra_body; drop_params=True would strip them)
_VLLM_EXTRA_BODY = {
    "top_k": 20,
    "min_p": 0.0,
    "repetition_penalty": 1.0,
    "chat_template_kwargs": {"enable_thinking": False},
}


class TunedLiteLLM(LiteLLM):
    def call(self, *args, **kwargs):
        for k, v in _OPENAI_SAMPLING.items():
            kwargs.setdefault(k, v)
        extra_body = dict(kwargs.pop("extra_body", None) or {})
        for k, v in _VLLM_EXTRA_BODY.items():
            extra_body.setdefault(k, v)
        kwargs["extra_body"] = extra_body
        try:
            return super().call(*args, **kwargs)
        except OutputLengthExceededError as e:
            truncated = getattr(e, "truncated_response", None)
            if truncated:
                return truncated
            raise


class TerminusWrapper(Terminus):
    def __init__(
        self,
        model_name: str,
        max_episodes: int = 50,
        api_base: str | None = None,
        temperature: float = 0.7,  # Qwen3.8-27B non-thinking recommendation
        **kwargs,
    ):
        super().__init__(
            model_name=model_name,
            max_episodes=max_episodes,
            api_base=api_base,
            temperature=temperature,
            **kwargs,
        )
        # Replace the stock LiteLLM with the tuned one (same constructor args).
        self._llm = TunedLiteLLM(
            model_name=model_name, api_base=api_base, temperature=temperature
        )
