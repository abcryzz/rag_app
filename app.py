import logging
import sys
import streamlit as st
import pathway as pw
import yaml
import requests
import threading 
from dotenv import load_dotenv
from pathway.udfs import DiskCache, ExponentialBackoffRetryStrategy
from pathway.xpacks.llm import embedders, llms, parsers, splitters
from pathway.xpacks.llm.question_answering import BaseRAGQuestionAnswerer
from pathway.xpacks.llm.vector_store import VectorStoreServer

# Step 1: Set Up Your License Key
# Replace 'YOUR_PATHWAY_LICENSE_KEY' with your actual license key.
pw.set_license_key("PATHWAY_LICENSE_KEY")

# Step 2: Configure Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(name)s %(levelname)s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

# Step 3: Load Environment Variables
load_dotenv()

# Step 4: Define Data Sources Function
def data_sources(source_configs):
    sources = []
    for source_config in source_configs:
        if source_config["kind"] == "local":
            # Read local files.
            source = pw.io.fs.read(
                **source_config["config"],
                format="binary",
                with_metadata=True,
            )
            sources.append(source)
        # Add other data source kinds if needed.
    return sources

# Step 5: Initialize RAG Application (Cached)
@st.cache_resource
def initialize_rag_app():
    try:
        # Load configuration settings from a YAML file.
        with open('config.yaml') as config_f:
            configuration = yaml.safe_load(config_f)

        # Extract the GPT model name from the configuration.
        llm_model = configuration["llm_config"]["model"]

        # Initialize Embedder
        embedder = embedders.SentenceTransformerEmbedder(
            model="avsolatorio/GIST-small-Embedding-v0",
        )

        # Initialize Chat Model
        chat = llms.LiteLLMChat(
            model=llm_model,
            retry_strategy=ExponentialBackoffRetryStrategy(max_retries=6),
            cache_strategy=DiskCache(),
            temperature=0.05,
        )

        # Set up Vector Store
        doc_store = VectorStoreServer(
            *data_sources(configuration["sources"]),
            embedder=embedder,
            splitter=splitters.TokenCountSplitter(max_tokens=400),
            parser=parsers.ParseUnstructured(),
        )

        # Set up RAG Application
        rag_app = BaseRAGQuestionAnswerer(llm=chat, indexer=doc_store)
        host_config = configuration["host_config"]
        host, port = host_config["host"], host_config["port"]
        rag_app.build_server(host=host, port=port)
        
        # Run the server in a separate thread
        threading.Thread(target=rag_app.run_server, kwargs={'with_cache': True, 'terminate_on_error': False}, daemon=True).start()

        logging.info("RAG Application initialized successfully.")
        return rag_app
    except Exception as e:
        logging.error(f"Failed to initialize RAG application: {e}")
        return None

def ask_question(question):
    url = 'http://localhost:8000/v1/pw_ai_answer'
    headers = {'accept': '*/*', 'Content-Type': 'application/json'}
    data = {'prompt': question}
    response = requests.post(url, headers=headers, json=data)
    return response.json()

# Step 6: Build Streamlit UI
def main():
    st.title("Retrieval Augmented Generation (RAG) Application")

    # Initialize RAG application
    rag_app = initialize_rag_app()

    # Input field for user question
    user_question = st.text_input("Enter your question:")

    if st.button("Submit"):
        if user_question:
            # Answer the question using the RAG application
            response = ask_question(user_question)

            # Display the answer
            st.subheader("Answer:")
            st.write(response)

            # Optionally display retrieved documents or sources
            # st.subheader("Retrieved Documents:")
            # st.write(retrieved_docs)
        else:
            st.warning("Please enter a question.")

if __name__ == "__main__":
    main()
