from dotenv import load_dotenv
from groq import Groq
import os
import json  # Add this import for JSON serialization
from sonalyse_advisor.config import MODEL
from sonalyse_advisor.json_utils import gather_all_extracted_data, load_json

load_dotenv()


def read_context_file(file_path: str) -> str:
    with open(file_path, "r") as file:
        return file.read()


def interpret_json(json_path: str, context_path: str,  accommodation_information_path : str) -> str:
    """Interpret the given JSON data using a language model with provided context.

    Args:
        json_path: The path to the JSON data to interpret.
        context_path: The path to the context file to provide to the model.

    Returns:
        The full response from the model.
    """
    client = Groq(api_key=os.environ["GROQ_API_KEY"])

    # Serialize JSON data to ensure proper formatting
    context_content = read_context_file(context_path)
    accommodation_info = json.dumps(load_json(accommodation_information_path), ensure_ascii=False)
    json_data = json.dumps(gather_all_extracted_data(json_path), ensure_ascii=False)

    oms_guide = read_context_file("data/OMS_guide.txt")
    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "system",
                "content": f"System Prompt : {context_content}, \n\n, OMS Guideline : {oms_guide}\n\n Information on the accommodation : {accommodation_info}\n\n JSON Data: \n\n {json_data}",
            },
            {
                "role": "user",
                "content": "Generate Python Streamlit code for my diagnostic. Use Streamlit functions like st.markdown, st.write, st.metric, etc.",
            },
        ],
        stream=False,  # Disable streaming to get the full result
        model=MODEL,
    )
    return chat_completion.choices[0].message.content  # Access attributes properly


def read_stream_response(stream_response: str) -> str:
    """Read and print the streaming response from the model.

    Args:
        stream_response: The streaming response object from the model.
    """
    for chunk in stream_response:
        if chunk.choices[0].delta.content is None:
            continue
        print(chunk.choices[0].delta.content, end="", flush=True)
