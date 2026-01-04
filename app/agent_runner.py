from app.agent import agent_executor, process_image_expense

async def run_agent(user_id: int, message_text: str = None, image_data: bytes = None) -> str:
    print(f"Running agent for user: {user_id}")
    
    if image_data:
        print("Processing Image...")
        return await process_image_expense(user_id, image_data)

    if message_text:
        result = await agent_executor.ainvoke(
            {
                "input": message_text,
                "user_id": user_id,
                "tool_names": ["record_expense", "get_expense_total"]
            }
        )
        return result["output"]

    return "No input received."