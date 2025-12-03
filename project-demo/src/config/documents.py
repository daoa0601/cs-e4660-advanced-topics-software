"""
Document loader for test files.

Provides utilities to load and parse test documents in various formats
(Python, YAML, JSON, HTML, Markdown, Terraform, PDF, etc.)
"""

import os
import json
from pathlib import Path
from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from enum import Enum


class DocumentType(Enum):
    """Types of documents that can be analyzed."""
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    YAML = "yaml"
    JSON = "json"
    HTML = "html"
    MARKDOWN = "markdown"
    TERRAFORM = "terraform"
    DOCKERFILE = "dockerfile"
    PDF = "pdf"
    TEXT = "text"
    UNKNOWN = "unknown"


# File extension to document type mapping
EXTENSION_MAP = {
    ".py": DocumentType.PYTHON,
    ".js": DocumentType.JAVASCRIPT,
    ".ts": DocumentType.JAVASCRIPT,
    ".yaml": DocumentType.YAML,
    ".yml": DocumentType.YAML,
    ".json": DocumentType.JSON,
    ".html": DocumentType.HTML,
    ".htm": DocumentType.HTML,
    ".md": DocumentType.MARKDOWN,
    ".markdown": DocumentType.MARKDOWN,
    ".tf": DocumentType.TERRAFORM,
    ".hcl": DocumentType.TERRAFORM,
    ".pdf": DocumentType.PDF,
    ".txt": DocumentType.TEXT,
}


@dataclass
class Document:
    """A loaded document with metadata."""
    path: str
    filename: str
    doc_type: DocumentType
    content: str
    size_bytes: int
    encoding: str = "utf-8"
    metadata: Optional[Dict[str, Any]] = None
    
    @property
    def extension(self) -> str:
        """Get file extension."""
        return Path(self.filename).suffix.lower()
    
    @property
    def title(self) -> str:
        """Get document title (filename without extension)."""
        return Path(self.filename).stem
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "path": self.path,
            "filename": self.filename,
            "type": self.doc_type.value,
            "content": self.content,
            "size_bytes": self.size_bytes,
            "encoding": self.encoding,
            "metadata": self.metadata,
        }


def detect_document_type(filepath: str) -> DocumentType:
    """Detect document type from file extension."""
    ext = Path(filepath).suffix.lower()
    
    # Check extension map first
    if ext in EXTENSION_MAP:
        return EXTENSION_MAP[ext]
    
    # Check for Dockerfile (no extension)
    filename = Path(filepath).name.lower()
    if filename == "dockerfile" or filename.startswith("dockerfile."):
        return DocumentType.DOCKERFILE
    
    return DocumentType.UNKNOWN


def load_document(filepath: str, encoding: str = "utf-8") -> Document:
    """
    Load a document from file.
    
    Args:
        filepath: Path to the document
        encoding: File encoding (default: utf-8)
    
    Returns:
        Document object with content and metadata
    """
    path = Path(filepath)
    
    if not path.exists():
        raise FileNotFoundError(f"Document not found: {filepath}")
    
    doc_type = detect_document_type(filepath)
    
    # Handle PDF differently (binary)
    if doc_type == DocumentType.PDF:
        return _load_pdf(filepath)
    
    # Load text-based documents
    with open(filepath, 'r', encoding=encoding) as f:
        content = f.read()
    
    size_bytes = path.stat().st_size
    
    # Parse metadata for specific types
    metadata = _extract_metadata(content, doc_type)
    
    return Document(
        path=str(path.absolute()),
        filename=path.name,
        doc_type=doc_type,
        content=content,
        size_bytes=size_bytes,
        encoding=encoding,
        metadata=metadata,
    )


def _load_pdf(filepath: str) -> Document:
    """Load a PDF document and extract text."""
    path = Path(filepath)
    size_bytes = path.stat().st_size
    
    # Try to extract text from PDF
    try:
        import fitz  # PyMuPDF
        doc = fitz.open(filepath)
        text_parts = []
        for page in doc:
            text_parts.append(page.get_text())
        content = "\n".join(text_parts)
        doc.close()
    except ImportError:
        # If PyMuPDF not available, return placeholder
        content = f"[PDF Document: {path.name} - {size_bytes} bytes]\n(PDF text extraction requires PyMuPDF)"
    except Exception as e:
        content = f"[PDF Document: {path.name}]\nError extracting text: {e}"
    
    return Document(
        path=str(path.absolute()),
        filename=path.name,
        doc_type=DocumentType.PDF,
        content=content,
        size_bytes=size_bytes,
        encoding="binary",
        metadata={"format": "pdf"},
    )


def _extract_metadata(content: str, doc_type: DocumentType) -> Optional[Dict[str, Any]]:
    """Extract metadata from document content."""
    metadata = {}
    
    if doc_type == DocumentType.PYTHON:
        # Extract docstring and imports
        lines = content.split('\n')
        imports = [l for l in lines if l.startswith('import ') or l.startswith('from ')]
        metadata['imports'] = imports[:10]  # First 10 imports
        metadata['line_count'] = len(lines)
        
    elif doc_type == DocumentType.JSON:
        try:
            parsed = json.loads(content)
            metadata['keys'] = list(parsed.keys()) if isinstance(parsed, dict) else []
        except json.JSONDecodeError:
            metadata['valid_json'] = False
            
    elif doc_type == DocumentType.YAML:
        # Count top-level keys
        lines = content.split('\n')
        top_keys = [l.split(':')[0] for l in lines 
                   if l and not l.startswith(' ') and not l.startswith('#') and ':' in l]
        metadata['top_level_keys'] = top_keys[:10]
        
    elif doc_type == DocumentType.HTML:
        # Extract title if present
        import re
        title_match = re.search(r'<title>(.*?)</title>', content, re.IGNORECASE)
        if title_match:
            metadata['html_title'] = title_match.group(1)
        
    elif doc_type == DocumentType.MARKDOWN:
        # Extract headers
        lines = content.split('\n')
        headers = [l for l in lines if l.startswith('#')]
        metadata['headers'] = headers[:10]
    
    return metadata if metadata else None


def load_all_documents(directory: str, recursive: bool = True) -> List[Document]:
    """
    Load all documents from a directory.
    
    Args:
        directory: Directory path
        recursive: Whether to search subdirectories
    
    Returns:
        List of Document objects
    """
    documents = []
    path = Path(directory)
    
    if not path.exists():
        raise FileNotFoundError(f"Directory not found: {directory}")
    
    pattern = "**/*" if recursive else "*"
    
    for filepath in path.glob(pattern):
        if filepath.is_file() and not filepath.name.startswith('.'):
            # Skip binary files we can't handle
            if filepath.suffix.lower() in ['.pyc', '.pyo', '.so', '.dll', '.exe']:
                continue
            try:
                doc = load_document(str(filepath))
                documents.append(doc)
            except Exception as e:
                print(f"Warning: Could not load {filepath}: {e}")
    
    return documents


def get_documents_by_type(
    documents: List[Document], 
    doc_type: DocumentType
) -> List[Document]:
    """Filter documents by type."""
    return [d for d in documents if d.doc_type == doc_type]


# =============================================================================
# Pre-defined Test Document Sets
# =============================================================================

# Base path for test documents
TEST_DOCUMENTS_DIR = Path(__file__).parent.parent.parent / "test_documents"


def get_test_document_path(relative_path: str) -> str:
    """Get absolute path to a test document."""
    return str(TEST_DOCUMENTS_DIR / relative_path)


def load_code_documents() -> List[Document]:
    """Load all code documents (Python, JS)."""
    return load_all_documents(str(TEST_DOCUMENTS_DIR / "code"))


def load_config_documents() -> List[Document]:
    """Load all configuration documents (YAML, JSON, Terraform, Docker)."""
    return load_all_documents(str(TEST_DOCUMENTS_DIR / "configs"))


def load_doc_documents() -> List[Document]:
    """Load all documentation (HTML, Markdown)."""
    return load_all_documents(str(TEST_DOCUMENTS_DIR / "docs"))


def load_report_documents() -> List[Document]:
    """Load all report documents (PDFs)."""
    return load_all_documents(str(TEST_DOCUMENTS_DIR / "reports"))


def load_all_test_documents() -> List[Document]:
    """Load all test documents from all categories."""
    documents = []
    
    for subdir in ["code", "configs", "docs", "reports"]:
        dir_path = TEST_DOCUMENTS_DIR / subdir
        if dir_path.exists():
            documents.extend(load_all_documents(str(dir_path)))
    
    return documents


# =============================================================================
# Document Catalog for Experiments
# =============================================================================

@dataclass 
class DocumentCatalogEntry:
    """Entry in the document catalog."""
    id: str
    name: str
    path: str
    doc_type: DocumentType
    category: str
    description: str
    expected_issues: List[str]


# Catalog of test documents with known issues
DOCUMENT_CATALOG: List[DocumentCatalogEntry] = [
    DocumentCatalogEntry(
        id="python_auth",
        name="User Authentication Module",
        path="code/user_auth.py",
        doc_type=DocumentType.PYTHON,
        category="code",
        description="Python authentication module with SQL injection and password storage issues",
        expected_issues=[
            "SQL injection in login()",
            "SQL injection in get_user_by_id()",
            "Plaintext password storage",
            "Missing commit in register()",
            "Hardcoded temporary password",
            "Sensitive data in logs",
            "Weak session ID generation (MD5)",
            "Debug function in production",
        ]
    ),
    DocumentCatalogEntry(
        id="python_api",
        name="Flask REST API",
        path="code/api_server.py",
        doc_type=DocumentType.PYTHON,
        category="code",
        description="Flask API server with multiple security vulnerabilities",
        expected_issues=[
            "No authentication on endpoints",
            "SQL injection",
            "Command injection",
            "Path traversal",
            "Unrestricted file upload",
            "Pickle deserialization (RCE)",
            "Unsafe YAML loading",
            "XSS vulnerability",
            "Open redirect",
            "Debug mode in production",
            "Overly permissive CORS",
            "Verbose error messages",
        ]
    ),
    DocumentCatalogEntry(
        id="k8s_deployment",
        name="Kubernetes Deployment",
        path="configs/kubernetes-deployment.yaml",
        doc_type=DocumentType.YAML,
        category="config",
        description="Kubernetes configuration with security misconfigurations",
        expected_issues=[
            "Secrets in plain text",
            "API keys in ConfigMap",
            "Debug mode enabled",
            "Using 'latest' tag",
            "SSH port exposed",
            "Hardcoded credentials in env",
            "Container running as privileged",
            "Container running as root",
            "No resource limits",
            "Host filesystem mounted",
            "Docker socket mounted",
            "Overly permissive NetworkPolicy",
            "cluster-admin bound to default SA",
        ]
    ),
    DocumentCatalogEntry(
        id="terraform_aws",
        name="AWS Terraform Configuration",
        path="configs/aws-infrastructure.tf",
        doc_type=DocumentType.TERRAFORM,
        category="config",
        description="Terraform AWS infrastructure with security issues",
        expected_issues=[
            "Hardcoded AWS credentials in provider",
            "Default password in variable",
            "Security group allows all inbound",
            "SSH open to world",
            "Database port open to world",
            "Secrets in user_data",
            "No IMDSv2 requirement",
            "Unencrypted EBS volume",
            "Public S3 bucket",
            "RDS publicly accessible",
            "Weak database password",
            "IAM policy with admin access (*/*)",
            "Skip final snapshot on RDS",
            "Sensitive values in outputs",
        ]
    ),
    DocumentCatalogEntry(
        id="html_login",
        name="Bank Login Page",
        path="docs/login-page.html",
        doc_type=DocumentType.HTML,
        category="web",
        description="HTML login page with client-side security issues",
        expected_issues=[
            "Loading scripts from HTTP",
            "Form action uses HTTP",
            "No CSRF token",
            "Autocomplete enabled for password",
            "SSN field on login page",
            "Hardcoded API keys in JavaScript",
            "Debug mode enabled",
            "Storing credentials in localStorage",
            "Credentials in URL parameters",
            "eval() with user data",
            "XSS vulnerability",
            "Insecure postMessage handler",
            "Hardcoded admin password",
            "Debug info in HTML comments",
        ]
    ),
    DocumentCatalogEntry(
        id="md_architecture",
        name="Architecture Specification",
        path="docs/architecture-spec.md",
        doc_type=DocumentType.MARKDOWN,
        category="docs",
        description="Architecture document with exposed credentials and compliance issues",
        expected_issues=[
            "Outdated software versions",
            "No rate limiting",
            "MD5 password hashing",
            "JWT secret in documentation",
            "API key in URL parameters",
            "HTTP internal communication",
            "No mTLS",
            "Plaintext password storage",
            "Full SSN stored",
            "CVV stored (PCI violation)",
            "Database credentials in docs",
            "Encryption at rest disabled",
            "TDE not implemented",
            "AWS credentials exposed",
            "SSH key in documentation",
            "Third-party API keys exposed",
            "Public S3 bucket for backups",
        ]
    ),
    DocumentCatalogEntry(
        id="json_config",
        name="Application Configuration",
        path="configs/app-config.json",
        doc_type=DocumentType.JSON,
        category="config",
        description="JSON configuration with hardcoded secrets",
        expected_issues=[
            "Debug mode enabled",
            "SSL disabled",
            "Weak CORS configuration",
            "Database password in config",
            "Weak JWT secret",
            "OAuth client secrets exposed",
            "API keys in config",
            "MD5 password hashing",
            "Stripe live keys exposed",
            "AWS credentials in config",
            "Email API keys exposed",
            "SMS auth tokens exposed",
            "Sentry sends PII",
            "Logging passwords enabled",
            "CSRF disabled",
            "XSS protection disabled",
            "Insecure cookie settings",
            "Admin backdoor enabled",
            "Admin password in config",
        ]
    ),
    DocumentCatalogEntry(
        id="docker_compose",
        name="Docker Compose Configuration",
        path="configs/docker-compose.yaml",
        doc_type=DocumentType.YAML,
        category="config",
        description="Docker Compose with container security issues",
        expected_issues=[
            "Running as root",
            "Hardcoded secrets in environment",
            "Docker socket mounted",
            "Host root filesystem mounted",
            "Shadow file mounted",
            "Privileged mode enabled",
            "All capabilities added",
            "No security options",
            "No resource limits",
            "Using 'latest' tag",
            "Database port exposed",
            "Redis without auth",
            "Default MongoDB credentials",
            "Elasticsearch security disabled",
            "Anonymous Grafana access as Admin",
            "Jenkins running as root",
        ]
    ),
    DocumentCatalogEntry(
        id="dockerfile",
        name="Application Dockerfile",
        path="configs/Dockerfile",
        doc_type=DocumentType.DOCKERFILE,
        category="config",
        description="Dockerfile with build and runtime security issues",
        expected_issues=[
            "Using 'latest' tag",
            "Running as root",
            "Hardcoded secrets in ARG/ENV",
            "Secrets in image layers",
            "Unnecessary packages (nmap, tcpdump)",
            "Overly permissive permissions (777)",
            "Bypassing SSL with --trusted-host",
            "Dev dependencies in production",
            "Private keys in image",
            "Secrets in bash history",
            "Too many ports exposed",
            "No health check",
            "No multi-stage build",
            "Shell form CMD",
        ]
    ),
    DocumentCatalogEntry(
        id="pdf_audit",
        name="Security Audit Report",
        path="reports/security-audit-q4-2024.pdf",
        doc_type=DocumentType.PDF,
        category="report",
        description="PDF security audit with exposed findings and credentials",
        expected_issues=[
            "Production credentials in report",
            "Database passwords exposed",
            "API keys listed",
            "SSH private key snippet",
            "AWS credentials exposed",
            "PCI compliance failures documented",
            "Admin access information",
            "Third-party service credentials",
        ]
    ),
    DocumentCatalogEntry(
        id="pdf_incident",
        name="Incident Report",
        path="reports/incident-report-2024-0042.pdf",
        doc_type=DocumentType.PDF,
        category="report",
        description="Security incident report with breach details",
        expected_issues=[
            "Vulnerable code snippets",
            "Attack vectors documented",
            "Old credentials in containment section",
            "Regulatory notification status",
            "Data compromise details",
        ]
    ),
]


def get_catalog_entry(doc_id: str) -> Optional[DocumentCatalogEntry]:
    """Get a catalog entry by ID."""
    for entry in DOCUMENT_CATALOG:
        if entry.id == doc_id:
            return entry
    return None


def load_catalog_document(doc_id: str) -> Document:
    """Load a document by catalog ID."""
    entry = get_catalog_entry(doc_id)
    if not entry:
        raise ValueError(f"Unknown document ID: {doc_id}")
    
    filepath = get_test_document_path(entry.path)
    return load_document(filepath)


def list_catalog() -> List[Dict[str, Any]]:
    """List all documents in the catalog."""
    return [
        {
            "id": e.id,
            "name": e.name,
            "type": e.doc_type.value,
            "category": e.category,
            "description": e.description,
            "expected_issue_count": len(e.expected_issues),
        }
        for e in DOCUMENT_CATALOG
    ]
