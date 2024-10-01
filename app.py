import logging
import sys
import streamlit as st
import pathway as pw
import yaml
import re
import os
import requests
import fitz
import threading 
from dotenv import load_dotenv
from pathway.udfs import DiskCache, ExponentialBackoffRetryStrategy
from pathway.xpacks.llm import embedders, llms, parsers, splitters
from pathway.xpacks.llm.prompts import prompt_short_qa,prompt_qa
from pathway.xpacks.llm.question_answering import BaseRAGQuestionAnswerer,AdaptiveRAGQuestionAnswerer
from pathway.xpacks.llm.vector_store import VectorStoreServer

# Step 1: Set Up Your License Key
pw.set_license_key("PATHWAY_LICENSE_KEY")

UPLOAD_FOLDER = 'data/pdfs'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

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


def remove_personal_info(text):
    # Remove email addresses
    text = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b', '[EMAIL REDACTED]', text)
    
    # Remove phone numbers (general patterns)
    text = re.sub(r'\b\d{10}\b', '[PHONE REDACTED]', text)  
    # International numbers with dashes/spaces
    text = re.sub(r'\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b', '[PHONE REDACTED]', text)  

    # Remove names (you can adjust this to target more specific names or use NLP libraries for named entity recognition)
    text = re.sub(r'\b[A-Z][a-z]*\s[A-Z][a-z]*\b', '[NAME REDACTED]', text)

    

    return text
def ask_question(question):
    url = 'http://localhost:8000/v1/pw_ai_answer'
    headers = {'accept': '*/*', 'Content-Type': 'application/json'}
    data = {'prompt': question}
    response = requests.post(url, headers=headers, json=data)
    return response.json()

def format_response(text):
    # Split long text into sections if needed (e.g., by paragraphs or periods)
    if text is None:
        return "No response available. thanks for asking"
    sections = text.split("\n\n")
    
    # Initialize a formatted string
    formatted_text = ""
    
    for section in sections:
        # Example: Adding bullet points if the section contains lists
        if "- " in section or "* " in section:
            formatted_text += f"\n\n{section}\n"
        else:
            # For regular text, add it as a paragraph with markdown
            formatted_text += f"\n\n{section}"
    
    # You can also format specific keywords like 'symptoms' or 'hopelessness' for readability
    formatted_text = formatted_text.replace("Symptoms", "### Symptoms")
    # formatted_text = formatted_text.replace("Hopelessness", "### Hopelessness")

    # Return the formatted markdown text
    return formatted_text




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
            temperature=.7
            ,
        )

        # Set up Vector Store
        doc_store = VectorStoreServer(
            *data_sources(configuration["sources"]),
            embedder=embedder,
            splitter=splitters.TokenCountSplitter(max_tokens=350),
            parser=parsers.ParseUnstructured(),
        )

        # Set up RAG Application
        rag_app = BaseRAGQuestionAnswerer(
            llm=chat,
            indexer=doc_store,
            short_prompt_template=lambda query, docs: prompt_short_qa(
                query, docs, additional_rules="Please respond to the following question in an encouraging, positive, and supportive tone, ensuring sensitivity toward the user's feelings and situation. Carefully consider the provided context, and address any specific concerns mentioned. If the question relates to a problem, offer constructive exercises or practical advice that can help the user effectively address their issue. Ensure your response is thorough and thoughtful, fostering a sense of understanding and support."

            ),
            long_prompt_template=lambda query, docs: prompt_qa(
                query, docs, additional_rules="Please respond to the following question in an encouraging, positive, and supportive tone, ensuring sensitivity toward the user's feelings and situation. Carefully consider the provided context, and address any specific concerns mentioned. If the question relates to a problem, offer constructive exercises or practical advice that can help the user effectively address their issue. Ensure your response is thorough and thoughtful, fostering a sense of understanding and support."

            ),
            search_topk=3
        )
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




# Step 6: Build Streamlit UI
def main():
    st.title("Nurture Your Mind, Embrace Your Heart.")

    # Initialize RAG application
    rag_app = initialize_rag_app()

    # PDF upload section
    uploaded_pdf = st.file_uploader("Upload a PDF file for reference:", type=["pdf"])
    
    if uploaded_pdf is not None:
        # Save the uploaded PDF directly to the 'data' folder
        file_path = os.path.join(UPLOAD_FOLDER, uploaded_pdf.name)
        with open(file_path, 'wb') as f:
            f.write(uploaded_pdf.getbuffer())  # Save the uploaded PDF
        
        st.success("PDF uploaded and saved successfully!")

    # Input field for user question
    user_question = st.text_input("Enter your thoughts or questions")

    if st.button("Submit"):
        if user_question:
            sanitized_question = remove_personal_info(user_question)
            # Answer the question using the RAG application
            response1 = ask_question(sanitized_question)

            # Display the answer
            response = format_response(response1)
            st.subheader("Answer:")
            st.write(response)
        else:
            st.warning("Please enter a question.")

if __name__ == "__main__":
    main()

