from dotenv import load_dotenv
from langchain.agents import create_agent
from ./
from rich import print

load_dotenv()

def call_agent(pergunta: str) -> str:
    agent = create_agent(
        model="google_genai:gemini-2.5-flash",
        system_prompt="Você é um Agente super legal",
    )

    result = agent.invoke(
        {"messages": [{"role": "user", "content": pergunta}]}
    )
    return result['messages'][-1].content

if __name__ == '__main__':
    pergunta = input("Digite sua pergunta: ")
    print(call_agent(pergunta))