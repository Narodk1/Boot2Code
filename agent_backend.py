from dotenv import load_dotenv
from groq import Groq
import os
from config import MODEL
from json_utils import load_json

load_dotenv()


def read_context_file(file_path: str) -> str:
    with open(file_path, "r") as file:
        return file.read()


def interpret_json(json: str, context: str) -> str:
    """Interpret the given JSON data using a language model with provided context.

    Args:
        json: The JSON data to interpret.
        context: The context to provide to the model.

    Returns:
        The streaming response from the model.
    """
    client = Groq(api_key=os.environ["GROQ_API_KEY"])

    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "system",
                "content": f"System Prompt : {read_context_file(context)}, \n\n JSON Data: \n\n {load_json(json)}",
            },
            {
                "role": "user",
                "content": "Give me my diagnostic.",
            },
        ],
        stream=True,
        model=MODEL,
    )
    return chat_completion


def read_stream_response(stream_response: str) -> str:
    """Read and print the streaming response from the model.

    Args:
        stream_response: The streaming response object from the model.
    """
    for chunk in stream_response:
        if chunk.choices[0].delta.content is None:
            continue
        print(chunk.choices[0].delta.content, end="", flush=True)
