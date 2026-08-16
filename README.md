# AI Travel Concierge - Team AGENTIC FOUR

An AI-powered travel assistant that uses an LLM and external APIs to provide
personalized and conversational travel recommendations and itinerary planning
through a web interface.

**Track:** A - Essential  
**Duration:** 8 Weeks  
**Team Size:** 4

## Team & Roles

| Name | Responsibility |
|---|---|
| Vaishnav R Menon | Repository setup and structure, collaborator management, project board, documentation |
| Jyoshita NH | API setup and management, development stack configuration |
| Ninad Gowda | Core RAG chatbot and AI/agent development |
| Parinitha Srinivas | Streamlit UI development and backend integration |

All team members will contribute to testing, deployment, integration and final
project documentation.

## Project Overview

We are building a Simple Travel Assistant that can understand travel-related
queries, retrieve relevant information using external APIs and tools, and
generate basic personalized itineraries.

The user will be able to provide requirements such as destination, duration,
budget, group size and interests. The system will process these requirements
and provide relevant travel information and an itinerary through a
conversational interface.

As development progresses, the project will be extended from a basic travel
assistant into a tool-using AI agent capable of selecting and using external
tools to complete travel-related tasks.

## Main Objectives

- Build a conversational AI travel assistant.
- Understand natural-language travel requirements.
- Integrate external travel-related APIs and tools.
- Generate personalized travel itineraries.
- Consider user preferences and constraints such as budget and duration.
- Allow users to refine their travel plans through follow-up queries.
- Provide a simple web interface using Streamlit.
- Store relevant user searches using a database.
- Handle API errors and invalid inputs appropriately.

## Planned Core Features

- Conversational travel assistant
- Travel information search
- External API and tool integration
- Destination recommendations
- Basic itinerary generation
- Budget-aware planning
- User preference handling
- Search history
- Streamlit web interface

Additional features will be considered after the core functionality is working.

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Streamlit |
| Backend | Python + LangChain |
| Database | SQLite |
| LLM | Gemini or other suitable LLM |
| APIs | 2 to 3 travel-related APIs/tools |
| Version Control | Git and GitHub |
| Deployment | Streamlit Cloud |

The exact APIs and LLM will be finalized after testing their availability,
limitations and suitability for the project.

## Proposed Architecture

```text
User
 |
 v
Streamlit Interface
 |
 v
AI Travel Agent
 |
 +----------------+----------------+
 |                |                |
 v                v                v
Search Tool   Travel API Tool   Other Tools
 |                |                |
 +----------------+----------------+
                  |
                  v
          Itinerary Generator
                  |
                  v
          Budget and Preference
               Handling
                  |
                  v
           Final Travel Plan
                  |
                  v
              SQLite DB
