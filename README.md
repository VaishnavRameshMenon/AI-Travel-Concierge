# TripPilot

# AI Travel Concierge - Team AGENTIC FOUR

An AI-powered travel assistant that uses an LLM and external APIs to provide
personalized travel recommendations and itinerary planning through a web
interface.

## Team & Roles

| Name | Responsibility |
|---|---|
| Vaishnav R Menon | Backend and project integration, GitHub repository and project management, documentation, testing and deployment coordination |
| Jyoshita NH | API setup and management, development stack configuration, API testing and secure API key handling |
| Ninad Gowda | Core RAG chatbot, LLM integration and AI/agent development |
| Parinitha Srinivas | Streamlit UI development and frontend/backend integration |

All team members will contribute to testing, debugging, deployment and final
project integration.

## Project Overview

We are building a Simple Travel Assistant that can understand travel-related
queries, retrieve relevant information using external APIs and tools, and
generate basic personalized itineraries.

The user will be able to provide details such as destination, duration,
budget, group size and interests. The system will process these requirements
and provide relevant travel information and an itinerary through a
conversational interface.

As development progresses, the project will be extended from a basic travel
assistant into a tool-using AI agent capable of selecting and using external
tools to complete travel-related tasks.

## Main Objectives

- Understand travel requirements expressed in natural language.
- Retrieve relevant travel information using external APIs and tools.
- Generate personalized day-by-day itineraries.
- Consider constraints such as budget, duration, group size and preferences.
- Allow users to modify and refine their itinerary through follow-up queries.
- Provide a simple web interface using Streamlit.
- Store relevant travel searches using a database.
- Handle API errors and invalid inputs appropriately.

## Planned Core Features

- Conversational travel assistant
- Travel information search
- External API and tool integration
- Destination recommendations
- Basic itinerary generation
- Budget-aware planning
- User preference and constraint handling
- Conversational itinerary modification
- Search history
- Streamlit web interface

Additional features will be considered after the core functionality is
working.

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
```


The architecture is a preliminary design and will be refined as development
progresses.

## Development Plan

### Week 1 to 2: Foundation

**Goal:** Set up the project and get the first working version running.

- Create and organize the GitHub repository.
- Set up collaborators and the project board.
- Set up the Python development environment.
- Configure LangChain and Streamlit.
- Research suitable travel APIs and tools.
- Set up secure API key handling.
- Build the initial RAG/chatbot foundation.
- Create the initial Streamlit interface.
- Test the basic AI interaction.
- Deploy the initial version if feasible.

**Milestone:** Basic working travel assistant prototype.

### Week 3 to 4: Core Agent Architecture

**Goal:** Move from a basic chatbot toward a tool-using AI agent.

- Integrate the selected search and travel tools.
- Implement tool calling with LangChain.
- Improve the agent's ability to select appropriate tools.
- Add basic error handling.
- Test the tools individually.
- Connect the agent with the Streamlit interface.
- Test different travel-related queries.

**Milestone:** Agent can use external tools to answer travel queries.

### Week 5 to 6: Travel Specialization

**Goal:** Add travel-specific functionality.

- Integrate the selected travel API or APIs.
- Add SQLite database functionality.
- Implement basic itinerary generation.
- Add budget and preference handling.
- Improve the travel planning workflow.
- Connect database and itinerary functionality to the UI.
- Improve API key and secret management.

**Milestone:** Working travel planning assistant with itinerary generation.

### Week 7 to 8: Finalization and Deployment

**Goal:** Improve the application and prepare the final version.

- Improve the Streamlit interface.
- Add input validation.
- Improve error handling.
- Add saving and export functionality if feasible.
- Perform end-to-end testing.
- Improve documentation.
- Deploy the final application.
- Prepare the final demonstration and presentation.

**Milestone:** Complete deployed AI Travel Concierge.

## Repository Structure

```text
AI-Travel-Concierge/
├── app.py
├── agent/
├── database/
├── tools/
├── utils/
├── tests/
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```

The repository structure will be updated as development progresses.

## Security

API keys and other sensitive information will not be committed to the
repository.

Environment variables and appropriate secret management methods will be used
for local development and deployment.

## Current Status

**Week 1: Planning and Initial Setup**

The team has finalized the AI Travel Concierge topic and discussed the
project objectives, proposed features, architecture, technology stack and
division of responsibilities.

The GitHub repository and project board have been created. Development and API
research will begin in the next phase.

## Submission Plan

The project will be developed and submitted progressively throughout the
8-week project period.

Weekly progress, source code and relevant documentation will be maintained in
this repository.

## Team

**Team AGENTIC FOUR**

1. Vaishnav R Menon
2. Jyoshita NH
3. Ninad Gowda
4. Parinitha Srinivas
