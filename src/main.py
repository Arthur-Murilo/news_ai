from langgraph.graph import StateGraph, MessagesState, START, END
from typing import cast

def mock_llm(state: MessagesState):
    return {"messages": [{"role": "ai", "content": "Iai tudo bem?"}]}

graph = StateGraph(MessagesState)
graph.add_node(mock_llm)
graph.add_edge(START, "mock_llm")
graph.add_edge("mock_llm", END)
graph = graph.compile()

response = graph.invoke(cast(MessagesState,{"messages": [{"role": "user", "content": "hi!"}]}))

print(response['messages'][1].content)