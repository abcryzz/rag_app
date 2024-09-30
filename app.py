import logging
import sys

import click
import pathway as pw
import yaml
from dotenv import load_dotenv
from pathway.udfs import DiskCache, ExponentialBackoffRetryStrategy
from pathway.xpacks.llm import embedders, llms, parsers, splitters
from pathway.xpacks.llm.question_answering import BaseRAGQuestionAnswerer
from pathway.xpacks.llm.vector_store import VectorStoreServer

# Step 1: Set Up Your License Key
# To access advanced features, get your free license key from https://pathway.com/features.
# Paste it below. For the community version, comment out the line below.
pw.set_license_key("PATHWAY_LICENSE_KEY")

# Step 2: Configure Logging
# This sets up logging to capture and display log messages. It's helpful for debugging.
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(name)s %(levelname)s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

# Step 3: Load Environment Variables
# Load variables from a .env file. This is useful for managing sensitive data like API keys.
load_dotenv()

# Step 4: Define Data Sources Function
# This function reads data from various sources like local files, Google Drive, or SharePoint.
def data_sources(source_configs) -> list[pw.Table]:
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
        elif source_config["kind"] == "gdrive":
            # Read files from Google Drive.
            source = pw.io.gdrive.read(
                **source_config["config"],
                with_metadata=True,
            )
            sources.append(source)
        elif source_config["kind"] == "sharepoint":
            try:
                import pathway.xpacks.connectors.sharepoint as io_sp
                # Read files from SharePoint.
                source = io_sp.read(**source_config["config"], with_metadata=True)
                sources.append(source)
            except ImportError:
                print(
                    "The Pathway Sharepoint connector is part of the commercial offering, "
                    "please contact us for a commercial license."
                )
                sys.exit(1)
    return sources

# Step 5: Define Main Function
# This function orchestrates the entire RAG pipeline using Click for command-line interaction.
@click.command()
@click.option("--config_file", default="config.yaml", help="Config file to be used.")
def run(config_file: str = "config.yaml"):
    # Load configuration settings from a YAML file.
    with open(config_file) as config_f:
        configuration = yaml.safe_load(config_f)

    # Extract the GPT model name from the configuration.
    llm_model = configuration["llm_config"]["model"]

    # Step 6: Initialize Embedder
    # The embedder converts text into embeddings, which are numerical representations of the text.
    embedder = embedders.SentenceTransformerEmbedder(
        model="avsolatorio/GIST-small-Embedding-v0",
        
    )

    # Step 7: Initialize Chat Model
    # Set up the language model for chat with retry strategy and cache.
    chat = llms.LiteLLMChat(
        model=llm_model,
        retry_strategy=ExponentialBackoffRetryStrategy(max_retries=6),
        cache_strategy=DiskCache(),
        temperature=0.05,
    )

    # Extract host and port configuration for the server.
    host_config = configuration["host_config"]
    host, port = host_config["host"], host_config["port"]

    # Step 8: Set Up Vector Store
    # The vector store server manages document embeddings and retrieval.
    doc_store = VectorStoreServer(
        *data_sources(configuration["sources"]),
        embedder=embedder,
        splitter=splitters.TokenCountSplitter(max_tokens=400),
        parser=parsers.ParseUnstructured(),
    )

    # Step 9: Set Up RAG Application
    # Combine retrieval and generation for question answering.
    rag_app = BaseRAGQuestionAnswerer(llm=chat, indexer=doc_store)

    # Step 10: Build and Run Server
    # Start the server to handle incoming requests.
    rag_app.build_server(host=host, port=port)
    rag_app.run_server(with_cache=True, terminate_on_error=False)

# If this script is executed directly, run the main function.
if __name__ == "__main__":
    run()

# Congratulations!
# You've set up the essential components of your RAG pipeline using Pathway.
# This setup allows you to read data from multiple sources, process it into embeddings,
# and use a GPT model to answer questions based on retrieved information.
