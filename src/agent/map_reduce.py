from dotenv import load_dotenv
load_dotenv()

from typing import Any, Dict
# import numpy as np
from agent.graph_state import State
import chromadb
from langchain_core.messages import AIMessage
from langgraph.types import Send

client = chromadb.CloudClient()


def continue_instructions(state: State):
    # creates one job per instruction — your existing approach
    return [Send("get_chunks", {"instruction": instr}) for instr in state["instructions"]] #send to get_chunks for each instruction


def get_chunks(state: State):
    """
    Called for a single instruction job. Expects state to contain "instruction".
    Queries Chroma for top-2 matches and appends a mapping into state["mapped_chunks"].
    """
    instruction = state.get("instruction")
    if instruction is None:
        raise ValueError("get_chunks expects state['instruction'] to be present")

    collection = client.get_collection(name="manim_source_code")
    results = collection.query(query_texts=[instruction], n_results=1) 

    ids = results.get("ids", [[]])[0]
    documents = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]

    chunks = []
    for i in range(len(documents)): #for all chunks of an instruction
        chunk = {
            "id": ids[i] if i < len(ids) else None,
            "text": documents[i],
            "metadata": metadatas[i] if i < len(metadatas) else {},
        }
        chunks.append(chunk)
    # print(chunks)
    # print(instruction)

    # store mapped result keyed by the instruction (append to mapped_chunks list)
    mapped = {"instruction": instruction, "chunks": chunks}
    # Return state and the chunks for downstream processing
    return {
        "mapped_chunks": [mapped]
    }

