# RAG-based Exam Prep and Emotional Support Model

## Overview

This repository contains a Retrieval-Augmented Generation (RAG) model designed to assist students during exam or quiz preparation by providing an interactive and supportive learning environment. The model not only enhances learning through the generation of practice questions but also detects when the user feels anxious or sad and offers emotionally supportive responses to keep the learning process positive and motivating.

## Features
* Learning Aid: Provides detailed explanations and can generate quiz or exam questions based on the material, helping users prepare more effectively.
* Practice Mode: Generates practice questions to test the user's understanding and reinforce key concepts.
*	Mood Detection: If the model detects that the conversation is taking a negative or anxious turn, it responds with supportive and motivational messages.
*	Adaptive Responses: Customizes its approach based on the user’s emotional state, combining educational and emotional support.
*	Document Retrieval: The model retrieves relevant documents or past information to assist with more comprehensive answers, using RAG (Retrieval-Augmented Generation).
How It Works
1.	Input: Users provide prompts related to their learning topics or ask questions that reflect their current study needs.
2.	Question Generation: The RAG model generates relevant questions based on the study material to help the user practice and deepen their understanding.
3.	Emotional Detection: The model monitors the conversation. If anxiety or stress is detected in the input, it generates an encouraging or soothing message.
4.	Answer Retrieval: The model can pull in relevant documents or previously encountered questions to provide answers or further context.
5.	Adaptability: By recognizing the emotional state, the model can switch between offering quiz-related assistance and emotional support seamlessly.
Why It’s a Game-Changer
During exam preparation, the stress and pressure to perform well can be overwhelming. This model aims to reduce that burden by:
•	Delivering a better learning experience through interactive practice questions.
•	Offering emotional support when stress or anxiety becomes noticeable in the conversation.
•	Keeping users focused and motivated by balancing learning with empathetic, supportive responses.

## Setup and Installation
* Clone the Repository:
  ```
  #!/bin/bash
  git clone https://github.com/abcryzz/rag_app.git
  cd rag_app
  
  ```
*Install the Required Dependencies: Make sure to install the dependencies listed in requirements.txt:
 ```
  pip install -r requirements.txt
 ```
*Set up API Keys: This project requires API access to Mistral and Pathway license key. Create a .env file to store your keys:
 ```
  PATHWAY_LICENSE_KEY=
  MISTRAL_API_KEY
 ```
*Run the Application: Start the application with:
 ```
  python app.py
 ```

## Usage
Once the app is running, you can interact with the model by providing prompts related to your exam or quiz preparation. Example interactions:

* Learning Assistance:

 * User: "Explain photosynthesis."
 * Model: "Photosynthesis is the process by which green plants and some other organisms use sunlight to synthesize foods with the help of chlorophyll..."

* Practice Mode:

 * User: "Can you give me some practice questions on photosynthesis?"
 * Model: "Sure! Here's a question: What is the primary product of photosynthesis?"
* Emotional Support:

 * User: "I don't think I’m going to do well in this exam, I'm too stressed."
 * Model: "It's okay to feel anxious sometimes, but remember how far you've come. Let’s break it down and focus on one topic at a time. You’ve got this!"
 
  
