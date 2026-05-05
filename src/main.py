from langgraph.graph import StateGraph, MessagesState, START, END
from typing import cast
from rich import print

def mock_llm(state: MessagesState):
    return {"messages": [{"role": "ai", "content": 'Teste2'}]}

def verification(state: MessagesState):
    messages = state["messages"]
    if messages[-1].content == 'Teste1':
        return {"messages": [{"role": "ai", "content": 'Funcionou'}]}
    else:
        return {"messages": [{"role": "ai", "content": 'Deu problema'}]}

graph = StateGraph(MessagesState)
graph.add_node(mock_llm)
graph.add_node(verification)
graph.add_edge(START, "mock_llm")
graph.add_edge('mock_llm', 'verification')
graph.add_edge("verification", END)
graph = graph.compile()

response = graph.invoke(cast(MessagesState,{"messages": [{"role": "user", "content": "hi!"}]}))

print(response)