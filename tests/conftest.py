import pytest
from langchain_core.messages import AIMessage

from lab.testing import ScriptedChatModel


@pytest.fixture
def scripted():
    """Factory: scripted(*messages) -> ScriptedChatModel that replays the given AIMessages."""
    def make(*messages):
        return ScriptedChatModel(script=list(messages) or [AIMessage(content="done")])
    return make
