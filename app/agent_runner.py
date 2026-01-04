from app.agent import agent_executor

async def run_agent(user_id: int, message: str) -> str:
    print(f"Running agent for user: {user_id}")
    
    result = await agent_executor.ainvoke(
        {
            "input": message,
            "user_id": user_id,
        }
    )
    return result["output"]