"""Stub tools — local replacements for SciSciGPT's GCP/Pinecone tools."""

from __future__ import annotations

from typing import Type
from pydantic import BaseModel, Field, create_model
from langchain.tools import BaseTool
from langchain_core.messages import ToolMessage


# --- Simple tool input schemas ---

class CodeInput(BaseModel):
    code: str = Field(..., description="Code to execute in the sandbox.")
    state: dict | None = Field(default=None, description="Agent state (ignored in stub).")


class SQLInput(BaseModel):
    query: str = Field(..., description="SQL query to execute.")
    state: dict | None = Field(default=None, description="Agent state.")


class SearchInput(BaseModel):
    query: str = Field(..., description="Search query string.")
    state: dict | None = Field(default=None, description="Agent state.")


# --- Stub tool implementations ---

class PythonJupyterStub(BaseTool):
    name: str = "python_jupyter"
    description: str = "Execute Python code in a Jupyter sandbox (stub)."
    args_schema: Type[BaseModel] = CodeInput

    def _run(self, code: str, state: dict | None = None) -> str:
        return '{"stdout": "Mock: code executed successfully", "result": "ok"}'

class RJupyterStub(BaseTool):
    name: str = "r_jupyter"
    description: str = "Execute R code in a sandbox (stub)."
    args_schema: Type[BaseModel] = CodeInput

    def _run(self, code: str, state: dict | None = None) -> str:
        return '{"stdout": "Mock: R code executed", "result": "ok"}'

class JuliaJupyterStub(BaseTool):
    name: str = "julia_jupyter"
    description: str = "Execute Julia code in a sandbox (stub)."
    args_schema: Type[BaseModel] = CodeInput

    def _run(self, code: str, state: dict | None = None) -> str:
        return '{"stdout": "Mock: Julia code executed", "result": "ok"}'

class SQLQueryStub(BaseTool):
    name: str = "sql_query_tool"
    description: str = "Execute SQL query (stub)."
    args_schema: Type[BaseModel] = SQLInput

    def _run(self, query: str, state: dict | None = None) -> str:
        return '{"columns": ["id", "value"], "rows": 0, "message": "Mock query executed"}'

class SQLSchemaStub(BaseTool):
    name: str = "sql_get_schema_tool"
    description: str = "Get table schema (stub)."
    args_schema: Type[BaseModel] = SQLInput

    def _run(self, query: str, state: dict | None = None) -> str:
        return '{"tables": ["papers", "authors", "citations"]}'

class SQLListTablesStub(BaseTool):
    name: str = "sql_list_table_tool"
    description: str = "List available tables (stub)."
    args_schema: Type[BaseModel] = SQLInput

    def _run(self, query: str, state: dict | None = None) -> str:
        return '{"tables": ["papers", "authors", "citations", "paper_fields", "paper_citations"]}'

class SearchNameStub(BaseTool):
    name: str = "search_name_tool"
    description: str = "Fuzzy search for institution/field names (stub)."
    args_schema: Type[BaseModel] = SearchInput

    def _run(self, query: str, state: dict | None = None) -> str:
        return f'{{"matches": [{{"name": "Mock Institution", "score": 0.95}}], "query": "{query}"}}'

class SearchLiteratureStub(BaseTool):
    name: str = "search_literature_advanced_tool"
    description: str = "Search scientific literature (stub)."
    args_schema: Type[BaseModel] = SearchInput

    def _run(self, query: str, state: dict | None = None) -> str:
        return f'{{"papers": [{{"title": "Mock Paper", "year": 2024, "abstract": "Mock abstract for: {query}"}}], "total": 1}}'


# --- Assemble tool sets matching SciSciGPT specialist assignments ---

database_specialist_tools = [
    SQLListTablesStub(), SQLSchemaStub(), SQLQueryStub(), SearchNameStub()
]
analytics_specialist_tools = [
    PythonJupyterStub(), RJupyterStub(), JuliaJupyterStub()
]
literature_specialist_tools = [
    SearchLiteratureStub()
]
evaluation_specialist_tools: list = []
