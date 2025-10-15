"""
Backend interface for iExplain frontend.
Provides high-level functions to interact with the core system.
"""

import sys
from pathlib import Path
from typing import Dict, Any, List, Optional
import json
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.config_loader import load_config
from core.llm_client import LLMClient
from core.agent import Agent, AgentConfig
from core.orchestrator import SingleAgentWorkflow, SequentialWorkflow, HierarchicalWorkflow
from tools.tool_registry import get_tools_for_agent
from tools import search_tools
from data.parsers import parse_text_log, parse_csv, parse_json, parse_ttl, extract_intent_summary
from data.indexer import LogIndexer
from data.retriever import Retriever


class BackendInterface:
    """High-level interface to iExplain backend for frontend use."""

    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize backend interface.

        Args:
            config: Optional configuration dict. If None, uses defaults.
        """
        self.config = config or self._load_default_config()
        self.llm_client = None
        self.retriever = None
        self.current_indexer = None

    def _load_default_config(self) -> Dict:
        """Load default configuration."""
        # Try to load a default config file
        config_path = Path(__file__).parent.parent.parent / "config"
        default_configs = ["baseline_single_agent.yaml", "sequential_two_agent.yaml"]

        for config_file in default_configs:
            full_path = config_path / config_file
            if full_path.exists():
                return load_config(str(full_path))

        # Fallback: minimal config
        return {
            "llm": {
                "provider": "anthropic",
                "model": "claude-sonnet-4-20250514"
            },
            "workflow": {
                "type": "single_agent",
                "agent_sequence": ["main"]
            },
            "agents": {
                "main": {
                    "system_prompt": "You are a helpful log analysis assistant.",
                    "tools": ["search_logs", "get_log_context"],
                    "max_tokens": 4096
                }
            },
            "data": {
                "index_method": "hybrid",
                "chunk_size": 1000,
                "chunk_overlap": 100
            }
        }

    def load_and_index_logs(
        self,
        log_path: str,
        method: str = "hybrid",
        chunk_size: int = 1000,
        overlap: int = 100
    ) -> Retriever:
        """
        Load and index log files.

        Args:
            log_path: Path to log file
            method: Indexing method ('simple', 'vector', or 'hybrid')
            chunk_size: Size of log chunks
            overlap: Overlap between chunks

        Returns:
            Retriever instance
        """
        # Parse logs based on file extension
        log_path = Path(log_path)

        if log_path.suffix == '.csv':
            documents = parse_csv(str(log_path))
        elif log_path.suffix in ['.json', '.jsonl']:
            documents = parse_json(str(log_path))
        else:
            parsed_logs = parse_text_log(str(log_path), parse_structured=True)
            documents = [
                {"line_number": log["line_number"], "raw_text": log["raw_text"]}
                for log in parsed_logs
            ]

        # Create indexers based on method
        if method == "hybrid":
            # Primary: vector, Secondary: keyword
            vector_indexer = LogIndexer(method="vector")
            keyword_indexer = LogIndexer(method="simple")

            vector_indexer.index(documents)
            keyword_indexer.index(documents)

            self.retriever = Retriever(
                indexer=vector_indexer,
                hybrid_indexer=keyword_indexer,
                hybrid_weight=0.6,
                chunk_size=chunk_size,
                overlap=overlap
            )
            self.current_indexer = vector_indexer

        else:
            # Simple or vector only
            indexer = LogIndexer(method=method)
            indexer.index(documents)

            self.retriever = Retriever(
                indexer=indexer,
                chunk_size=chunk_size,
                overlap=overlap
            )
            self.current_indexer = indexer

        # Set retriever for search tools
        search_tools.set_retriever(self.retriever)

        return self.retriever

    def run_workflow(
        self,
        task: str,
        log_source: str,
        workflow_type: str = "sequential",
        intent_source: Optional[str] = None,
        provider: str = "anthropic",
        model: str = "claude-sonnet-4-20250514",
        custom_agents: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Execute a workflow on logs.

        Args:
            task: Task description
            log_source: Path to log file
            workflow_type: Type of workflow ('single_agent', 'sequential', 'hierarchical')
            intent_source: Optional path to intent specification
            provider: LLM provider
            model: LLM model name
            custom_agents: Optional custom agent configurations

        Returns:
            Result dictionary with analysis output
        """
        # Initialize LLM client
        self.llm_client = LLMClient(provider=provider)

        # Use custom agents or defaults
        agents_config = custom_agents or self.config.get("agents", {})

        # Create agents
        agents = {}
        for agent_name, agent_cfg in agents_config.items():
            tool_registry = get_tools_for_agent(agent_cfg["tools"])

            agent_config = AgentConfig(
                name=agent_name,
                model=model,
                system_prompt=agent_cfg["system_prompt"],
                tools=agent_cfg["tools"],
                max_tokens=agent_cfg.get("max_tokens", 4096),
                temperature=agent_cfg.get("temperature")
            )

            agent = Agent(agent_config, self.llm_client, tool_registry)
            agents[agent_name] = agent

        # Create workflow
        workflow_config = {
            "type": workflow_type,
            "agent_sequence": list(agents.keys())
        }

        if workflow_type == "single_agent":
            workflow = SingleAgentWorkflow(agents, workflow_config)
        elif workflow_type == "sequential":
            workflow = SequentialWorkflow(agents, workflow_config)
        elif workflow_type == "hierarchical":
            workflow = HierarchicalWorkflow(agents, workflow_config)
        else:
            raise ValueError(f"Unknown workflow type: {workflow_type}")

        # Prepare data
        data = {
            "log_source": log_source,
            "intent_source": intent_source
        }

        # Execute workflow
        result = workflow.execute(task, data)

        return result

    def search_logs(
        self,
        query: str,
        k: int = 10,
        use_hybrid: bool = False
    ) -> List[Dict]:
        """
        Search indexed logs.

        Args:
            query: Search query
            k: Number of results
            use_hybrid: Whether to use hybrid search

        Returns:
            List of matching documents
        """
        if self.retriever is None:
            raise ValueError("No logs indexed. Call load_and_index_logs() first.")

        return self.retriever.retrieve(query, k=k, use_hybrid=use_hybrid)

    def load_intent(self, intent_path: str) -> Dict[str, Any]:
        """
        Load and parse an intent specification.

        Args:
            intent_path: Path to intent TTL file

        Returns:
            Intent metadata dictionary
        """
        graph = parse_ttl(intent_path)
        summary = extract_intent_summary(graph)

        # Also load natural language description if available
        intent_dir = Path(intent_path).parent
        txt_file = intent_dir / f"{intent_dir.name}.txt"

        nl_description = ""
        if txt_file.exists():
            with open(txt_file, 'r') as f:
                nl_description = f.read()

        return {
            "ttl_path": intent_path,
            "txt_description": nl_description,
            "structured": summary,
            "name": intent_dir.name
        }

    def get_available_intents(self) -> List[Dict[str, Any]]:
        """
        Get list of all available intents.

        Returns:
            List of intent metadata dictionaries
        """
        intents = []
        intents_path = Path(__file__).parent.parent.parent / "data" / "intents"

        if not intents_path.exists():
            return intents

        for item in intents_path.iterdir():
            if item.is_dir():
                ttl_file = item / f"{item.name}.ttl"
                if ttl_file.exists():
                    try:
                        intent_data = self.load_intent(str(ttl_file))
                        intents.append(intent_data)
                    except Exception as e:
                        print(f"Error loading intent {item.name}: {e}")

        return intents

    def get_index_stats(self) -> Dict[str, Any]:
        """
        Get statistics about current index.

        Returns:
            Statistics dictionary
        """
        if self.current_indexer is None:
            return {}

        return self.current_indexer.get_stats()

    def get_retriever_stats(self) -> Dict[str, Any]:
        """
        Get statistics about current retriever.

        Returns:
            Statistics dictionary
        """
        if self.retriever is None:
            return {}

        return self.retriever.get_stats()
