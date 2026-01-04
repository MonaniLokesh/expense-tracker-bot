from langchain_groq import ChatGroq
from langchain_classic.agents import AgentExecutor, create_react_agent
from langchain_core.prompts import PromptTemplate
from app.tools import record_expense, get_expense_total
import os
from dotenv import load_dotenv

load_dotenv()

text_model = ChatGroq(
    model="llama-3.3-70b-versatile",
    temperature=0
)

tools = [record_expense, get_expense_total]

prompt = PromptTemplate.from_template(
    """Answer the user's request.

Current User ID: {user_id}

You have access to the following tools:
{tools}

RULES:
1. To record an expense, you MUST pass a valid JSON string. Example: {{"user_id": 123, "amount": 10, "category": "food"}}
2. **IF THE USER SAYS "HELLO", "HI", OR CHATS CASUALLY:** Do NOT use a tool. Just skip directly to "Final Answer".

Use the following format:

Question: the input question you must answer
Thought: you should always think about what to do
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: the final answer to the original input question

Begin!

Question: {input}
Thought:{agent_scratchpad}"""
)

agent = create_react_agent(llm=text_model, tools=tools, prompt=prompt)

agent_executor = AgentExecutor(
    agent=agent,
    tools=tools,
    verbose=True,
    handle_parsing_errors=True
)
