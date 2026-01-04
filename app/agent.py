import base64
from langchain_core.messages import HumanMessage
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

vision_model = ChatGroq(
    model="meta-llama/llama-4-scout-17b-16e-instruct",
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

async def process_image_expense(user_id: int, image_data: bytes):
    """
    Uses Groq's Vision model to analyze the receipt.
    """
    b64_image = base64.b64encode(image_data).decode("utf-8")

    message = HumanMessage(
        content=[
            {
                "type": "text",
                "text": (
                    f"Analyze this receipt image. "
                    f"Extract the total amount and a category (e.g., food, transport, bills). "
                    f"The User ID is {user_id}. "
                    f"Return ONLY a JSON string compatible with the record_expense tool. "
                    f"Format: {{\"user_id\": {user_id}, \"amount\": 10.0, \"category\": \"food\", \"description\": \"item name\"}}"
                ),
            },
            {
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{b64_image}"},
            },
        ]
    )

    try:
        response = await vision_model.ainvoke([message])
        content = response.content.replace("```json", "").replace("```", "").strip()
        
        start_idx = content.find("{")
        end_idx = content.rfind("}") + 1
        if start_idx != -1 and end_idx != -1:
            json_str = content[start_idx:end_idx]
            result = record_expense.invoke(json_str)
            return f"Receipt processed! {result}"
        else:
            return "Could not find valid JSON in the vision model's response."
            
    except Exception as e:
        return f"Error processing image with Groq: {str(e)}"