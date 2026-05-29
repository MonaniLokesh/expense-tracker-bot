import base64
from datetime import date
import httpx
from langchain_core.messages import HumanMessage
from langchain_groq import ChatGroq
from langchain_classic.agents import AgentExecutor, create_react_agent
from app.config import TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN
from app.constants import GROQ_MODEL, LLM_TEMPERATURE, AGENT_VERBOSE
from app.prompt import REACT_AGENT_PROMPT, vision_receipt_text
from app.tools import ALL_TOOLS, record_expense

llm = ChatGroq(model=GROQ_MODEL, temperature=LLM_TEMPERATURE)

tool_names = [t.name for t in ALL_TOOLS]

agent = create_react_agent(llm=llm, tools=ALL_TOOLS, prompt=REACT_AGENT_PROMPT)
agent_executor = AgentExecutor(
    agent=agent, tools=ALL_TOOLS, verbose=AGENT_VERBOSE, handle_parsing_errors=True
)

async def download_twilio_media(media_url: str) -> bytes:
    """Download WhatsApp image from Twilio using Basic auth."""
    async with httpx.AsyncClient() as client:
        r = await client.get(
            media_url,
            auth=(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN),
            follow_redirects=True,
        )
        r.raise_for_status()
        return r.content

async def process_image_expense(user_id: int, image_data: bytes):
    """Extract receipt fields with Groq vision and save via record_expense."""
    today = str(date.today())
    b64_image = base64.b64encode(image_data).decode("utf-8")
    message = HumanMessage(
        content=[
            {"type": "text", "text": vision_receipt_text(user_id, today)},
            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64_image}"}},
        ]
    )
    try:
        response = await llm.ainvoke([message])
        content = response.content.replace("```json", "").replace("```", "").strip()
        start, end = content.find("{"), content.rfind("}") + 1
        if start == -1 or end <= start:
            return "Could not parse receipt."
        result = record_expense.invoke(content[start:end])
        return f"Receipt processed! {result}"
    except Exception as e:
        return f"Error processing image: {e}"
