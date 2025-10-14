# Understanding the Data Layer

The data layer is responsible for turning raw log files into something useful. This involves three main stages: parsing the logs into structured data, building an index for fast searching, and providing intelligent retrieval with context. Let's walk through each of these stages to understand how they work together.

## The Problem We're Solving

Imagine you have a log file with thousands or millions of entries. An agent needs to find relevant information to answer a question like "Why did the API response time increase?" Simply reading through every log line would be too slow and would exceed the LLM's context window. We need a way to quickly find the most relevant entries and present them with enough context to be useful.

## Stage 1: Parsing

Parsing is the process of taking raw text and extracting structure from it. Different log formats require different parsing strategies.

### Text Logs

OpenStack logs, like most system logs, follow a common pattern:

```
2017-05-16 00:00:04.500 2931 INFO nova.compute.manager [req-3ea4...] VM Started
```

When we parse this, we can extract several structured fields:
- Timestamp: When the event occurred
- Process ID: Which process logged this
- Level: INFO, ERROR, WARNING, etc.
- Component: Which part of the system generated the log
- Message: The actual log content

We use regular expressions to identify these patterns. The parser is flexible enough to handle logs that don't follow this exact pattern - it will still capture the raw text even if it can't extract all the structured fields.

### CSV and JSON Logs

Some systems output logs in structured formats like CSV or JSON. For these, parsing is straightforward - we use standard libraries (pandas for CSV, json for JSON) and convert each entry into a dictionary with named fields. The key is maintaining a consistent structure so that later stages don't need to worry about which format the logs came from.

### Intent Specifications

TMForum intent specifications use RDF/Turtle format, which is quite different from logs. These files describe what system administrators want to achieve - things like "API response time should be under 250ms". We parse these using the rdflib library, which understands RDF graphs, and then extract the key pieces of information: the intent description, the expectations, the conditions that define success, and the context where these apply.

## Stage 2: Indexing

Once logs are parsed, we need to make them searchable. The goal is to quickly answer questions like "Which log entries mention 'nova' and 'error'?"

### How Inverted Indexing Works

The fundamental data structure is an inverted index, which you can think of as a book's index. Instead of reading the whole book to find mentions of a topic, you look it up in the index to find which pages discuss it.

For logs, we build a similar structure. We go through each log entry and extract all the meaningful words (tokens). For each word, we record which log entries contain it. So we end up with something like:

```
"error" → [entry 15, entry 127, entry 389, ...]
"nova" → [entry 12, entry 15, entry 98, ...]
"timeout" → [entry 389, entry 401, ...]
```

When someone searches for "nova error", we find the entries that appear in both lists. This is much faster than scanning through every log entry.

### Tokenization

Before building the index, we need to turn log text into tokens. We convert everything to lowercase (so "Error" and "error" are treated the same), split on whitespace and punctuation, and extract individual words. More sophisticated tokenization could handle things like "API-error" or stem words to their roots, but we start with the simple approach that works well in practice.

### Scoring Results

When we find matching entries, we need to rank them by relevance. Currently we use a simple scoring method: count how many of the search terms appear in each entry. If you search for "nova compute error" and one entry contains all three terms while another contains only two, the first entry scores higher.

This simple approach works surprisingly well, especially for log analysis where you're typically looking for specific technical terms. More sophisticated scoring (like TF-IDF) can be added later if experiments show it would help.

## Stage 3: Retrieval

The retriever adds two important capabilities on top of the indexer: chunking for large log files and context windows for understanding results.

### Chunking

Large log files need to be processed in chunks. If you have a million log entries, you can't feed them all to an LLM at once. The retriever automatically splits logs into manageable chunks of, say, 1000 entries each.

But there's a subtle issue: what if something interesting happens at the boundary between chunks? You might miss the connection between events if they're split across chunks. To handle this, we use overlapping chunks. The last 100 entries of one chunk are also the first 100 entries of the next chunk. This overlap ensures that related events stay together in at least one chunk.

When the retriever returns search results, it annotates each result with which chunk it came from. This makes it easy to retrieve the entire chunk if an agent needs more context.

### Context Windows

Finding a single relevant log line is often not enough - you need to understand what was happening before and after. The retriever provides context windows: given a log entry, it can return N entries before and after it.

For example, if the agent finds a log line about an error, it can request a context window to see:
- What led up to the error (the 5 lines before)
- The error itself (marked clearly)
- What happened after (the 5 lines after)

This context is crucial for understanding root causes. An error message by itself might say "Connection timeout", but the preceding lines might show multiple retry attempts with increasing delays, giving a much clearer picture of what went wrong.

## Putting It Together

Here's how these stages work together in practice:

When an experiment starts, the system loads and parses the log file. This might take a few seconds for large files, but it only happens once. The parsed entries are stored in memory with their structured fields.

The indexer then processes these entries, building its inverted index. This preprocessing means that later searches will be fast - we're doing the expensive work upfront so that each individual search can be quick.

When an agent searches for something, the request goes through the retriever, which uses the indexer to find matches. The retriever adds chunk information and can provide context windows when needed. The agent receives a list of relevant log entries with enough context to understand them.

Throughout this process, the goal is to make logs accessible to LLMs. Raw log files are too large and unstructured. By parsing, indexing, and intelligently retrieving with context, we transform logs into focused, relevant information that an agent can reason about effectively.

## Design Choices

Several design choices shape how the data layer works:

**Memory vs. disk trade-offs:** Currently we keep parsed logs in memory for speed. This works well for files up to a few hundred MB. For larger files, we might need to use disk-based storage, but we haven't encountered that need yet in our experiments.

**Simple before complex:** We start with keyword-based search rather than vector embeddings. Keyword search is easier to understand, debug, and explain. If experiments show that semantic search would help, the architecture makes it easy to add a vector-based indexer alongside the simple one.

**Preserving provenance:** Every result includes its line number and source file. This traceability is important for research - you can always go back to the original log to verify what the agent found.

**Structure when available, text when not:** We try to extract structured fields like timestamps and log levels, but we always preserve the raw text. This dual representation means we can use structure when it helps (like filtering by log level) but fall back to text search when needed.

These choices reflect a pragmatic approach: use simple, proven techniques; optimize for the common case; but design for future extension when needed.
