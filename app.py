import os
from urllib.parse import urlparse
import secrets

import voyageai
from flask import Flask, request
from dotenv import load_dotenv
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pinecone import Pinecone
from mistralai.client import MistralClient

from dbbuilder import build_vector_database
from rag import WordPressRAG


load_dotenv()
app = Flask(__name__)
app.secret_key = secrets.token_hex()
DATABASE = Pinecone(os.environ["PINECONE_API_KEY"]).Index("wordpress-chatbot")
EMBEDDER = voyageai.Client(os.environ["VOYAGE_API_KEY"])
LLM_CLIENT = MistralClient(os.environ["MISTRAL_API_KEY"])
CHATBOT = WordPressRAG(LLM_CLIENT, "open-mistral-7b", EMBEDDER, DATABASE)


def authorize():
    auth = request.authorization
    if auth is None or auth.token != os.environ["AUTH_KEY"]:
        return {"message": "Wrong or no authentication key present."}, 401
    return {"message": "Authorization successful."}, 200


@app.route("/db", methods=["POST", "DELETE"])
def db_ops():
    """
    Request Body:
        {
            "site_url": "https://www.example.com",
            "create_if_not_present": true
        }

    Optional:
        "create_if_not_present": false (Default)
    """
    auth_res = authorize()
    if auth_res[1] == 401:
        return auth_res

    if "site_url" not in request.json:
        return {"message": "'site_url' is not present in the request body."}, 400
    site_domain = urlparse(request.json["site_url"]).hostname
    if not site_domain:
        return {"message": "'site_url' is not an url."}, 400

    match request.method:
        case "POST":
            EMBEDDING_SIZE = 1024
            match = DATABASE.query(
                namespace=site_domain,
                vector=[0]*EMBEDDING_SIZE,
                top_k=1,
            )["matches"]
            if len(match) == 1:
                return {
                    "message": f"Database already present for '{site_domain}'",
                    "database_present": True,
                    "database_created": False,
                }
            elif len(match) > 1:
                raise AssertionError("Only one match should've been returned.")

            if not request.json.get("create_if_not_present", False):
                return {
                    "message": f"Database not present for '{site_domain}'",
                    "database_present": False,
                    "database_created": False,
                }

            build_vector_database(
                request.json["site_url"],
                RecursiveCharacterTextSplitter.from_tiktoken_encoder(
                    encoding_name="cl100k_base", chunk_size=200, chunk_overlap=40
                ),
                EMBEDDER,
                DATABASE,
            )
            return {
                "message": f"Database created for '{site_domain}'",
                "database_present": True,
                "database_created": True,
            }

        case "DELETE":
            DATABASE.delete(delete_all=True, namespace=site_domain)
            return {"message": f"Database deleted for '{site_domain}'"}


@app.route("/chat", methods=["POST"])
def chat():
    """
    Request Body:
        {
            "site_url": "https://www.example.com",
            "messages": [
                {"role": "assistant", "content": "message1"},
                {"role": "system", "content": "message2"},
                {"role": "user", "content": "message3"}
            ]
        }
    """
    auth_res = authorize()
    if auth_res[1] == 401:
        return auth_res

    site_domain = urlparse(request.json["site_url"]).hostname
    return CHATBOT.generate(site_domain, request.json["messages"])
