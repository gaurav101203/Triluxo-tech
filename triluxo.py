# Ensure your VertexAI credentials are configured
import os
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "./GOOGLE_APPLICATION_CREDENTIALS.json"


from google.oauth2 import service_account
from google.auth.transport.requests import Request

credentials = service_account.Credentials.from_service_account_file(
    "./GOOGLE_APPLICATION_CREDENTIALS.json",
    scopes=["https://www.googleapis.com/auth/cloud-platform"]
)
credentials.refresh(Request())

from google.cloud import aiplatform as vertexai

vertexai.init(
    project="rag-model-448019",  # Replace with your Google Cloud project ID
    location="us-central1",
    credentials=credentials
)

from langchain_google_vertexai import ChatVertexAI

llm = ChatVertexAI(model="gemini-1.5-pro-001")

from langchain_google_vertexai import VertexAIEmbeddings

embeddings = VertexAIEmbeddings(model="text-embedding-005")

from langchain_core.vectorstores import InMemoryVectorStore

vector_store = InMemoryVectorStore(embeddings)

import nltk
nltk.download('punkt_tab')
nltk.download('averaged_perceptron_tagger_eng')

import bs4
from langchain import hub
from langchain_community.document_loaders import UnstructuredURLLoader
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langgraph.graph import START, StateGraph
from typing_extensions import List, TypedDict
import os

urls = ["https://brainlox.com/courses/category/technical"]
loader = UnstructuredURLLoader(urls=urls)

docs = loader.load()
text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
all_splits = text_splitter.split_documents(docs)

# Index chunks
_ = vector_store.add_documents(documents=all_splits)

# Define prompt for question-answering
prompt = hub.pull("rlm/rag-prompt")


# Define state for application
class State(TypedDict):
    question: str
    context: List[Document]
    answer: str

# Define application steps
def retrieve(state: State):
    retrieved_docs = vector_store.similarity_search(state["question"])
    return {"context": retrieved_docs}


def generate(state: State):
    docs_content = "\n\n".join(doc.page_content for doc in state["context"])
    messages = prompt.invoke({"question": state["question"], "context": docs_content})
    response = llm.invoke(messages)
    return {"answer": response.content}

# Compile application and test
graph_builder = StateGraph(State).add_sequence([retrieve, generate])
graph_builder.add_edge(START, "retrieve")
graph = graph_builder.compile()

from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

@app.route("/chatbot", methods=["POST"])
def chatbot():
    try:
        data = request.get_json() 
        question = data.get("question", "")

        if not question:
            return jsonify({"error": "Question is required"}), 400

        response = graph.invoke({"question": question})
        answer = response.get("answer", "No answer found.")

        return jsonify({"answer": answer})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000,debug=True)

