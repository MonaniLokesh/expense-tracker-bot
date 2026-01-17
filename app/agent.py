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
    """You are an advanced financial assistant bot designed to help users track their expenses.

Current User ID: {user_id}

You have access to the following instruments:
{tools}

To use a tool, please use the following format:

```
Thought: Do I need to use a tool? Yes
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
```

When you have a response for the user, or if you do not need to use a tool, you MUST use the format:

```
Thought: Do I need to use a tool? No
Final Answer: [your response here]
```

GUIDELINES:

1. **Recording Expenses**:
   - If the user says "I spent 100 on food" or "Add 50 for taxi", extract the `amount`, `category`, and optional `description`.
   - You MUST call the `record_expense` tool with a valid JSON string.
   - Example Action Input: {{"user_id": {user_id}, "amount": 100, "category": "food", "description": "lunch"}}

2. **Querying Expenses**:
   - If the user asks "How much did I spend?" or "Total for food?", use the `get_expense_total` tool.
   - Example Action Input: {{"user_id": {user_id}, "time_range": "all_time"}} (or specific range/category if applicable)

3. **Casual Conversation & Help**:
   - If the user says "Hello", "Hi", "Help", or asks what you can do:
   - Do NOT use any tools.
   - If he greets then just greet him back and ask him how can you help him.
   - Simply respond with a helpful message explaining your capabilities.
   - Example Answer: "Hello! I am your personal expense tracker. You can tell me things like 'I spent Rs.10 on coffee' or ask 'What is my total spending?'"

4. **Unclear Requests**:
   - If the user says something vague or unrelated (e.g., "The weather is nice"), politely guide them back to expense tracking.
   - Example Final Answer: "I'm here to help with your finances! Try telling me about a recent purchase."

Current Conversation:
{chat_history}

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