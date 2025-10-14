# iExplain Documentation

This folder contains documentation explaining how iExplain works and how to use it. The documentation is organized to help you understand both the system architecture and practical usage.

## Documentation Structure

**[architecture.md](architecture.md)** provides an overview of the system design. Start here to understand the big picture - why the system is structured the way it is, how the different components relate to each other, and what design principles guide the implementation. This document explains the reasoning behind architectural choices and helps you understand how the pieces fit together.

**[data-layer.md](data-layer.md)** explains how logs and intents are processed. This document walks through the three stages of data handling: parsing different formats into structured data, indexing for fast search, and intelligent retrieval with context. Read this to understand how raw log files become accessible information that agents can reason about.

**[agents-and-workflows.md](agents-and-workflows.md)** describes how agents work and how they can be orchestrated. This covers the agent reasoning loop, tool calling mechanisms, and different workflow patterns (single-agent, sequential, hierarchical). Understanding this is key to configuring effective experiments.

**[running-experiments.md](running-experiments.md)** is your practical guide to conducting research with iExplain. It explains how to create configuration files, run experiments, interpret results, and design comparative studies. This is where theory meets practice.

## Reading Guide

If you're new to the project, read the documents in order. Each builds on concepts from the previous ones.

If you're looking for specific information:
- Configuration help → running-experiments.md
- Data processing questions → data-layer.md
- Agent behavior questions → agents-and-workflows.md
- System design questions → architecture.md

## Documentation Philosophy

This documentation aims to be pedagogical rather than encyclopedic. Instead of listing every function and parameter, it explains how things work and why they're designed that way. The goal is understanding, not just reference.

Code comments and docstrings provide reference documentation for specific functions. This higher-level documentation explains concepts and patterns that span multiple files.

The documentation uses narrative explanation rather than bullet points where possible, because understanding how components interact requires following chains of reasoning rather than scanning lists of features.

## Keeping Documentation Updated

As the system evolves, documentation should evolve with it. When adding new features or changing how things work, update the relevant documentation. The documentation lives in version control alongside the code, making it easy to keep them synchronized.

If you find documentation that's unclear or outdated, improving it helps everyone who comes after you.
