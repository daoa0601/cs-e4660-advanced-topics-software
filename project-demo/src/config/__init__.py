"""
Configuration module.

Exports:
- Model configuration and pricing
- Prompt templates with A/B testing support
- Test data (queries, documents, contexts)
"""

from dotenv import load_dotenv
load_dotenv()

from .models import (
    GCP_PROJECT_ID,
    GCP_REGION,
    MODEL_PRICING,
    MODEL_IDS,
    get_model_id,
    get_pricing,
)

from .prompts import (
    PromptVariant,
    PromptTemplate,
    ABTestConfig,
    PROMPT_REGISTRY,
    PREDEFINED_AB_TESTS,
    get_prompt,
    register_prompt,
    list_prompts,
    get_ab_test,
    # Standard prompt templates
    GENERATION_PROMPTS,
    CRITIQUE_PROMPTS,
    REFINEMENT_PROMPTS,
    EXTRACTION_PROMPTS,
    SUMMARIZATION_PROMPTS,
    ANALYSIS_PROMPTS,
    VALIDATION_PROMPTS,
)

from .test_data import (
    VERBOSITY_QUERIES,
    SHORT_CONTEXT,
    LONG_CONTEXT,
    TECHNICAL_DOCUMENTS,
    TECHNICAL_DOCUMENTS_INLINE,
    get_technical_documents,
    REACT_QUERIES,
    MULTITURN_INITIAL_QUERIES,
    MULTITURN_FOLLOWUPS_3,
    MULTITURN_FOLLOWUPS_5,
    SELF_CORRECTING_TASKS,
    DOCUMENT_ANALYSIS_QUERY,
)

from .documents import (
    DocumentType,
    Document,
    DocumentCatalogEntry,
    DOCUMENT_CATALOG,
    detect_document_type,
    load_document,
    load_all_documents,
    get_documents_by_type,
    get_test_document_path,
    load_code_documents,
    load_config_documents,
    load_doc_documents,
    load_report_documents,
    load_all_test_documents,
    get_catalog_entry,
    load_catalog_document,
    list_catalog,
)

# Domain-specific prompt templates
from .prompt_templates import (
    DOMAINS,
    DomainConfig,
    PromptTemplate as DomainPromptTemplate,
    get_domain,
    list_domains,
    generate_experiment_prompts,
)

# Default experiment settings
DEFAULT_ITERATIONS = 20
DELAY_BETWEEN_CALLS = 0.5
DEFAULT_WORKERS = 4

# Database path
from pathlib import Path
DB_PATH = Path(__file__).parent.parent.parent / "data" / "experiments.db"

__all__ = [
    # GCP
    "GCP_PROJECT_ID",
    "GCP_REGION",
    # Models
    "MODEL_PRICING",
    "MODEL_IDS", 
    "get_model_id",
    "get_pricing",
    # Prompts
    "PromptVariant",
    "PromptTemplate",
    "ABTestConfig",
    "PROMPT_REGISTRY",
    "PREDEFINED_AB_TESTS",
    "get_prompt",
    "register_prompt",
    "list_prompts",
    "get_ab_test",
    "GENERATION_PROMPTS",
    "CRITIQUE_PROMPTS",
    "REFINEMENT_PROMPTS",
    "EXTRACTION_PROMPTS",
    "SUMMARIZATION_PROMPTS",
    "ANALYSIS_PROMPTS",
    "VALIDATION_PROMPTS",
    # Domain-specific prompts
    "DOMAINS",
    "DomainConfig",
    "DomainPromptTemplate",
    "get_domain",
    "list_domains",
    "generate_experiment_prompts",
    # Test data
    "VERBOSITY_QUERIES",
    "SHORT_CONTEXT",
    "LONG_CONTEXT",
    "TECHNICAL_DOCUMENTS",
    "TECHNICAL_DOCUMENTS_INLINE",
    "get_technical_documents",
    "REACT_QUERIES",
    "MULTITURN_INITIAL_QUERIES",
    "MULTITURN_FOLLOWUPS_3",
    "MULTITURN_FOLLOWUPS_5",
    "SELF_CORRECTING_TASKS",
    "DOCUMENT_ANALYSIS_QUERY",
    # Document loader
    "DocumentType",
    "Document",
    "DocumentCatalogEntry",
    "DOCUMENT_CATALOG",
    "detect_document_type",
    "load_document",
    "load_all_documents",
    "get_documents_by_type",
    "get_test_document_path",
    "load_code_documents",
    "load_config_documents",
    "load_doc_documents",
    "load_report_documents",
    "load_all_test_documents",
    "get_catalog_entry",
    "load_catalog_document",
    "list_catalog",
    # Settings
    "DEFAULT_ITERATIONS",
    "DELAY_BETWEEN_CALLS",
    "DEFAULT_WORKERS",
    "DB_PATH",
]
