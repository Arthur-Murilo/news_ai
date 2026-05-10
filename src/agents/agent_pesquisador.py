from dotenv import load_dotenv
from langchain.agents import create_agent
from src.prompts.agent_pesquisador_prompt import get_system_prompt
from src.agents.tools.search_tool import search_new
from rich import print 

load_dotenv()

def call_agent(pergunta: str) -> str:
    agent = create_agent(
        model="google_genai:gemini-2.5-flash",
        tools=[search_new],
        system_prompt=get_system_prompt(),
    )

    result = agent.invoke(
        {"messages": [{"role": "user", "content": pergunta}]}
    )
    return result['messages'][-1].content[0].get('text')

if __name__ == '__main__':
    pergunta = input("Digite sua pergunta: ")
    print(call_agent(pergunta))