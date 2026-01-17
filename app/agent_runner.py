from app.agent import agent_executor, process_image_expense

CHAT_HISTORY = {}

def get_formatted_history(user_id: int) -> str:
    history = CHAT_HISTORY.get(user_id, [])
    if not history:
        return "No previous conversation."
    return "\n".join(history)

def update_history(user_id: int, user_input: str, agent_output: str):
    if user_id not in CHAT_HISTORY:
        CHAT_HISTORY[user_id] = []
    
    entry = f"User: {user_input}\nAI: {agent_output}"
    CHAT_HISTORY[user_id].append(entry)
    
    if len(CHAT_HISTORY[user_id]) > 10:
        CHAT_HISTORY[user_id].pop(0)

async def run_agent(user_id: int, message_text: str = None, image_data: bytes = None) -> str:
    print(f"Running agent for user: {user_id}")
    
    if image_data:
        print("Processing Image...")
        return await process_image_expense(user_id, image_data)

    if message_text:
        history_str = get_formatted_history(user_id)
        
        result = await agent_executor.ainvoke(
            {
                "input": message_text,
                "user_id": user_id,
                "chat_history": history_str,
                "tool_names": ["record_expense", "get_expense_total"]
            }
        )
        output = result["output"]
        
        # Update history
        update_history(user_id, message_text, output)
        
        return output

    return "No input received."