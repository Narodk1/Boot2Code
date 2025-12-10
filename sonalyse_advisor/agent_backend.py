from dotenv import load_dotenv
from groq import Groq
import os
from config import MODEL
from json_utils import gather_all_extracted_data

load_dotenv()


def read_context_file(file_path: str) -> str:
    with open(file_path, "r") as file:
        return file.read()


def interpret_json(json_path: str, context_path: str) -> str:
    """Interpret the given JSON data using a language model with provided context.

    Args:
        json_path: The path to the JSON data to interpret.
        context_path: The path to the context file to provide to the model.

    Returns:
        The streaming response from the model.
    """
    client = Groq(api_key=os.environ["GROQ_API_KEY"])

    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "system",
                "content": f"System Prompt : {read_context_file(context_path)}, \n\n JSON Data: \n\n {gather_all_extracted_data(json_path)}",
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
