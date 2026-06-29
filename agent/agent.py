"""
Cardinal Court — voice receptionist agent.

Structured after LiveKit's official examples (basics/listen_and_respond +
basics/tool_calling): an Agent subclass with a @function_tool method, an
AgentServer entrypoint, and VAD prewarming.

STT/LLM/TTS route through LiveKit Inference, so only LiveKit Cloud credentials
are needed (LIVEKIT_URL / LIVEKIT_API_KEY / LIVEKIT_API_SECRET).
"""
import logging
import os
import sys

from dotenv import load_dotenv
from livekit.agents import (
    Agent,
    AgentSession,
    AgentServer,
    JobContext,
    JobProcess,
    RunContext,
    cli,
    function_tool,
    inference,
)
from livekit.plugins import silero

sys.path.insert(0, os.path.dirname(__file__))
from knowledge import build_system_prompt, lookup_tenant as _kb_lookup

load_dotenv()

logger = logging.getLogger("cardinal-court")
logger.setLevel(logging.INFO)


class CardinalCourtReceptionist(Agent):
    def __init__(self) -> None:
        super().__init__(instructions=build_system_prompt())

    @function_tool
    async def lookup_tenant(self, context: RunContext, name: str) -> str:
        """Look up which floor a company or tenant is on at Cardinal Court.

        Call this when a visitor asks about a specific company by name.
        Returns floor and notes, or a not-found message if the company is
        not in the building.

        Args:
            name: Company or tenant name to look up.
        """
        result = _kb_lookup(name)
        if result is None:
            return f"No listing for '{name}' at Cardinal Court."
        parts = [f"Floor {result['floor']}: {result['occupant']}."]
        if result.get("notes"):
            parts.append(result["notes"])
        if result.get("requires_id"):
            parts.append("They require photo ID from visitors.")
        return " ".join(parts)

    async def on_enter(self):
        # Greet the visitor as soon as the agent joins the room.
        self.session.generate_reply(
            instructions=(
                "Greet the visitor briefly and warmly, one or two sentences. "
                "For example: 'Good morning, welcome to Cardinal Court. "
                "How can I help you today?'"
            )
        )


server = AgentServer()


def prewarm(proc: JobProcess):
    # Load the VAD model once per worker process, not per session.
    proc.userdata["vad"] = silero.VAD.load()


server.setup_fnc = prewarm


@server.rtc_session()
async def entrypoint(ctx: JobContext):
    ctx.log_context_fields = {"room": ctx.room.name}

    session = AgentSession(
        stt=inference.STT(model="deepgram/nova-3"),
        llm=inference.LLM(model="openai/gpt-4.1-mini"),
        tts=inference.TTS(model="cartesia/sonic-3"),
        vad=ctx.proc.userdata["vad"],
        preemptive_generation=True,
    )

    await session.start(agent=CardinalCourtReceptionist(), room=ctx.room)
    await ctx.connect()


if __name__ == "__main__":
    cli.run_app(server)
