# iExplain Architecture

## Overview

iExplain is a research system designed to analyze system logs and explain what happened, especially in the context of administrative intents. The core idea is to use LLM-powered agents to understand log data and provide clear explanations about system behavior, whether things went as expected or if there were issues.

The system is built around three main concepts: **agents** that reason about logs, a **data layer** that makes logs searchable and understandable, and **workflows** that orchestrate how agents work together. Everything is driven by YAML configuration files, making it easy to run different experiments without changing code.

## Why This Architecture?

The architecture reflects several key goals:

**Research-focused design:** Since this is a research project, we need to track everything that happens during experiments. Every agent interaction, every tool call, and every decision is logged in detail. This allows researchers to analyze not just the final results, but understand how the system arrived at those conclusions.

**Provider independence:** We support multiple LLM providers (Anthropic, OpenAI, Ollama) through a unified interface. The choice of provider is just a configuration setting, not something baked into the code. This makes it easy to compare how different models perform on the same task.

**Modular composition:** The system is built from independent pieces that can be tested and understood separately. Parsers handle different log formats, indexers make logs searchable, and retrievers add intelligent chunking. Agents use these components through well-defined tool interfaces. This modularity makes it easier to improve one part without breaking others.

## System Layers

The system is organized into distinct layers, each with a clear responsibility.

### Core Layer

The core layer provides the fundamental building blocks for agent-based log analysis.

**LLMClient** serves as the bridge to various language model providers. It takes a model name, messages, and optional tools, then returns a standardized response regardless of which provider is being used. This standardization is crucial because different providers have slightly different APIs and response formats. The client handles these differences internally, so the rest of the system doesn't need to worry about whether it's talking to Claude, GPT, or a local Ollama model.

**Agent** is where the intelligence lives. An agent combines an LLM with a set of tools it can use. When you give an agent a task, it thinks about what to do, potentially calls tools to gather information or perform actions, and then continues reasoning based on the results. This loop continues until the agent has completed its task or reached a maximum number of iterations. Each agent has its own system prompt that defines its personality and approach, and its own set of available tools.

**Workflow** orchestrates how agents work together. The simplest workflow is single-agent, where one agent handles everything. Sequential workflows pass information through a chain of specialized agents. Future hierarchical workflows will have a supervisor agent that coordinates other agents. The workflow layer is responsible for managing this coordination and collecting all the execution traces for later analysis.

### Data Layer

The data layer transforms raw log files into something agents can work with effectively.

**Parsers** understand different log formats. Text logs get parsed line-by-line with optional extraction of structured fields like timestamps and log levels. CSV and JSON logs are parsed into structured records. TTL (Turtle) files containing TMForum intent specifications are parsed into RDF graphs. The key insight here is that logs come in many formats, and we need to handle them all while presenting a consistent interface to the rest of the system.

**Indexer** makes logs searchable. Currently we use a simple but effective approach: build an inverted index that maps each word to the documents (log lines) containing it. When you search for "error nova", the indexer finds all documents containing both words and ranks them by relevance. This is much faster than scanning through every log line, especially for large log files. The design allows for adding vector-based search later, but we start with the simpler approach that works well for most cases.

**Retriever** adds intelligence on top of the indexer. Large log files are split into overlapping chunks, which helps preserve context when retrieving information. When an agent asks for context around a specific log entry, the retriever can provide the surrounding lines. This context is often crucial for understanding what was happening in the system at that moment.

### Tool Layer

Tools are functions that agents can call to interact with the world. Each tool has a name, description, and parameter schema that the LLM can understand.

File tools let agents read files and list directory contents. This is essential for exploring available log files or reading configuration files.

Search tools provide the interface to the data layer. Agents can search logs using keywords and get back relevant entries. They can also request context windows around interesting log lines.

Intent tools work with TMForum intent specifications. These tools parse TTL files, extract expectations and conditions, and format them in a way that agents can understand. This allows agents to compare what was supposed to happen (the intent) with what actually happened (the logs).

The tool interface is standardized using OpenAI's function calling format, which most modern LLMs understand. Each tool defines what parameters it accepts and what it returns, making it clear to both the LLM and human readers what the tool does.

### Configuration System

Everything in iExplain is configured through YAML files. An experiment configuration specifies which LLM to use, what workflow pattern to follow, how agents are configured, and where to find the data.

This configuration-driven approach has several benefits. Experiments are reproducible because the complete setup is captured in a file. Comparing different approaches (like single-agent vs. multi-agent) just requires changing the configuration. The configuration files also serve as documentation of what each experiment is testing.

The system automatically generates timestamps for experiments and redacts API keys when saving results, making it safe to share experiment outputs without exposing credentials.

## Data Flow

Understanding how data flows through the system helps clarify how the pieces fit together.

When you run an experiment, the system first loads the configuration and validates it. It initializes the LLM client with the chosen provider and sets up any necessary authentication.

Next, it processes the input data. Log files are parsed into structured documents, and these documents are indexed for fast searching. If an intent specification is provided, it's parsed into a structured format. This preprocessing step is crucial because it transforms raw data into something the agents can work with efficiently.

The workflow then executes according to its type. In a single-agent workflow, one agent receives the task and all the data context. The agent reasons about what to do, potentially calling tools to search logs or parse intents, and produces a final explanation. In a sequential workflow, each agent performs a specialized role - one might focus on finding relevant logs, another on analyzing patterns, and a third on synthesizing an explanation.

Throughout execution, everything is logged. Each LLM call, each tool invocation, and each piece of reasoning is captured with timestamps. This detailed logging is what makes research possible - you can go back and understand exactly what the agent was thinking at each step.

Finally, results are saved in a comprehensive JSON file that includes the configuration, the complete execution trace, and the final output. This single file contains everything needed to understand and reproduce the experiment.

## Design Principles

Several principles guide the implementation:

**Start simple, add complexity when needed.** The indexer starts with keyword search because it's simple and works well. If experiments show that semantic search would help, it's easy to add vector embeddings later. Similarly, we implement single-agent workflows first, then move to multi-agent patterns.

**Make the implicit explicit.** Rather than hardcoding behavior, we make choices visible through configuration. The temperature setting, token limits, and even which tools an agent can use are all explicit configuration choices that can be varied across experiments.

**Optimize for understanding.** The code is structured to be readable and the system behavior to be traceable. Variable names are descriptive, functions do one thing well, and the extensive logging makes it possible to understand what happened during an experiment.

**Keep components independent.** The parser doesn't know about the indexer, and the indexer doesn't know about agents. Each component has a clear interface and can be tested independently. This independence makes the codebase easier to maintain and extend.

These principles work together to create a system that's both powerful enough for research and simple enough to understand and modify.
