import sys
import os
import asyncio
from dotenv import load_dotenv
import json

# Add the parent dir to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.sessions import SnowflakeConnector
from dbCreator import CortexSearchModule



# Load environment variables
load_dotenv()


if __name__ == "__main__":
    _connector = SnowflakeConnector()
    _create = input("Do You want to create new Database with a pdf Y/N:  ")

    # If the user chooses 'Y', ask for a PDF path, validate its existence, and parse it using CortexSearchModule.
    # If the file doesn't exist, notify the user. Handle any exceptions gracefully. Otherwise, abort the operation.
    if _create == 'Y' or _create == 'y':
        _pdf_path = input("Specify your path for the PDF (give absolute path):  ")
        try:
            if os.path.exists(_pdf_path) and os.path.isfile(_pdf_path):
                _cortex_search = CortexSearchModule(_connector, _pdf_path)
                asyncio.run(_cortex_search.run())
                print("Successfully parsed PDF data!")
            else:
                print(f"The file '{_pdf_path}' does not exist.")
        except Exception as err:
            print(f"Some error occurred: {err}")
    else:
        print("Operation aborted as per your choice.")


# construct prompt for LLM. It takes question and context as a input and returns prompt
def construct_prompt(question: str, context: str) -> str:
    prompt = f"""
    You are an expert legal advisor that extracts information from the Context provided. Answer the question below based on the provided context. 
    Ignore special characters, formatting issues, or irrelevant text.
    When ansering the question contained in Question be concise and do not hallucinate. 
    Only anwer the question if you can extract it from the CONTEXT provideed.       
    Do not mention the Context used in your answer.

    Context:
    {context}

    Question: {question}
    Answer:
    """
    return prompt



# Function to take user questions and fetches relevant information from a database,
# processes it, and generates an AI-powered response using a language model
async def RAG(question: str, root, session):
    if not root and session:
        return "Something unexpected happened. Please try again."
    else:
        my_service = (
            root.databases[os.environ["SNOWFLAKE_DATABASE"]]
            .schemas[os.environ["SNOWFLAKE_SCHEMA"]]
            .cortex_search_services[os.environ["SNOWFLAKE_CORTEX_SEARCH_SERVICE"]]
        )
        response = my_service.search(
            query=question, columns=["CHUNKS"], limit=5
        )
        # converting the response data into json format
        response_data = json.loads(response.json())
        context = ""
        for i in range(len(response_data["results"])):
            context += response_data["results"][i]["CHUNKS"]

        # constructing prompt and connecting to llm model using sql in snowflake 
        prompt = construct_prompt(question, context)
        cmd = """select snowflake.cortex.complete(?, ?) as response"""
        model = 'mistral-large2'
        result = session.sql(cmd, params=[model, prompt]).collect()
        llm_output = result[0]['RESPONSE']
        return llm_output



__all__ = ["RAG"]

