from dotenv import load_dotenv
from langchain.agents import create_agent
from src.prompts.agent_pesquisador_prompt import SYSTEM_PROMPT
from rich import print 

load_dotenv()

def call_agent(pergunta: str) -> str:
    agent = create_agent(
        model="google_genai:gemini-2.5-flash",
        system_prompt=SYSTEM_PROMPT,
    )

    result = agent.invoke(
        {"messages": [{"role": "user", "content": pergunta}]}
    )
    return result['messages'][-1].content

if __name__ == '__main__':
    pergunta = input("Digite sua pergunta: ")
    print(call_agent(pergunta))