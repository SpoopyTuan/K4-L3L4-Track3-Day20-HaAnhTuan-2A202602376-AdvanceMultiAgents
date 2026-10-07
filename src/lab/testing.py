"""PROVIDED - do not edit. A scripted fake chat model for OFFLINE tests (no API call, no token).

    model = ScriptedChatModel(script=[AIMessage(content="", tool_calls=[...]), AIMessage(content="done")])

Each call to the model returns the next message of `script` (the last one repeats).
After a run you can inspect `model.tool_names` / `model.tool_descriptions` (tools offered to the model) and
`model.system_prompts` (system prompt of every call) and `model.prompts` (user text of every call).
"""
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage
from langchain_core.outputs import ChatGeneration, ChatResult


class ScriptedChatModel(BaseChatModel):
    script: list = []
    tool_names: list = []
    tool_descriptions: dict = {}
    system_prompts: list = []
    prompts: list = []
    calls: int = 0

    @property
    def _llm_type(self) -> str:
        return "scripted-fake"

    def bind_tools(self, tools, **kwargs):
        names = []
        for t in tools:
            if isinstance(t, dict):
                name = t.get("name") or t.get("function", {}).get("name")
                desc = t.get("description") or t.get("function", {}).get("description", "")
            else:
                name = getattr(t, "name", getattr(t, "__name__", "?"))
                desc = getattr(t, "description", "") or ""
            names.append(name)
            self.tool_descriptions[name] = desc
        self.tool_names[:] = names
        return self

    def _generate(self, messages, stop=None, run_manager=None, **kwargs):
        self.prompts.append("\n".join(str(m.content) for m in messages if m.type == "human"))
        first = messages[0]
        self.system_prompts.append(str(first.content) if first.type == "system" else "")
        msg = self.script[min(self.calls, len(self.script) - 1)]
        self.calls += 1
        msg = msg.model_copy(update={
            "usage_metadata": {"input_tokens": 100, "output_tokens": 20, "total_tokens": 120},
            "response_metadata": {"model_name": "scripted-fake"},
        })
        return ChatResult(generations=[ChatGeneration(message=msg)])
