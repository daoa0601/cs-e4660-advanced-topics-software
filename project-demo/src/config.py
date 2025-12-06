"""
Configuration and model pricing for LLM Cost MVP.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Google Cloud Configuration
GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID")
GCP_REGION = os.getenv("GCP_REGION", "us-central1")

# Database - use session path if available
def _get_db_path():
    """Get database path from session or default."""
    try:
        from .session import get_session_db_path
        return get_session_db_path()
    except ImportError:
        pass
    return Path(os.getenv("DB_PATH", "data/experiments.db"))

DB_PATH = _get_db_path()

# Experiment defaults
DEFAULT_ITERATIONS = int(os.getenv("DEFAULT_ITERATIONS", "20"))
DELAY_BETWEEN_CALLS = float(os.getenv("DELAY_BETWEEN_CALLS", "0.5"))

# =============================================================================
# Model Pricing (per 1M tokens, as of Jan 2025)
# =============================================================================

MODEL_PRICING = {
    "gemini-2.5-flash": {
        "input_per_1m": 0.15,
        "output_per_1m": 0.60,
    },
    "gemini-2.5-pro": {
        "input_per_1m": 1.25,
        "output_per_1m": 5.00,
    },
    "flash": {
        "input_per_1m": 0.15,
        "output_per_1m": 0.60,
    },
    "pro": {
        "input_per_1m": 1.25,
        "output_per_1m": 5.00,
    },
}

MODEL_IDS = {
    "flash": "gemini-2.5-flash",
    "pro": "gemini-2.5-pro",
    "gemini-2.5-flash": "gemini-2.5-flash",
    "gemini-2.5-pro": "gemini-2.5-pro",
}

# =============================================================================
# Workflow Configurations
# =============================================================================

WORKFLOWS = {
    "verbosity": {
        "name": "Verbosity Tax Analysis",
        "description": "Compare concise vs chain-of-thought prompts",
        "pipelines": ["verbosity_concise", "verbosity_cot", "hybrid_cot"],
    },
    "context": {
        "name": "Context Length Analysis", 
        "description": "Compare short vs long input contexts",
        "pipelines": ["context_short", "context_long"],
    },
    "agentic": {
        "name": "Agentic Workflow Analysis",
        "description": "ReAct agents, conversations, self-correcting loops",
        "pipelines": ["react_research", "react_hybrid", "multiturn_3", 
                      "multiturn_5", "self_correcting", "self_correcting_hybrid"],
    },
    "document": {
        "name": "Technical Document Analysis",
        "description": "Analyze technical documents for issues, bugs, and security vulnerabilities",
        "pipelines": ["doc_analysis_simple", "doc_analysis_thorough", "doc_analysis_iterative"],
    },
}

# =============================================================================
# Test Data: Verbosity Workflow
# =============================================================================

VERBOSITY_QUERIES = [
    "What causes rain?",
    "Explain how a car engine works.",
    "Why is the sky blue?",
    "How does a computer store data?",
    "What is photosynthesis?",
    "Explain the concept of gravity.",
    "How do airplanes fly?",
    "What causes earthquakes?",
    "How does the internet work?",
    "Explain how vaccines work.",
]

PROMPT_TEMPLATES = {
    "concise": "Answer the following question in 1-2 sentences:\n\n{query}",
    "cot": "Think step by step and explain your reasoning thoroughly:\n\n{query}",
}

# =============================================================================
# Test Data: Context Workflow
# =============================================================================

SHORT_CONTEXT = """
The company reported Q3 earnings of $2.5 billion, up 15% year-over-year.
Revenue growth was driven primarily by cloud services.
Operating margin improved to 28% from 25% last year.
"""

LONG_CONTEXT = """
The company reported Q3 earnings of $2.5 billion, up 15% year-over-year, 
exceeding analyst expectations of $2.3 billion. Revenue growth was driven 
primarily by cloud services, which saw a 32% increase compared to the same 
quarter last year. The cloud division now accounts for 45% of total revenue, 
up from 38% in the prior year period.

Operating margin improved to 28% from 25% last year, reflecting cost 
optimization initiatives and economies of scale in the cloud infrastructure 
business. The company reduced headcount by 5% during the quarter as part of 
a broader restructuring effort announced in Q1.

Geographic breakdown shows North America contributing 55% of revenue, 
Europe 25%, and Asia-Pacific 20%. The Asia-Pacific region showed the 
strongest growth at 22% year-over-year, driven by expansion in India 
and Southeast Asian markets.

The company announced a new $10 billion share buyback program and 
increased its quarterly dividend by 10% to $0.55 per share. Management 
reaffirmed full-year guidance of $10-10.5 billion in revenue and 
projected continued margin expansion into Q4.

Key risks highlighted include currency headwinds, with the strong dollar 
expected to reduce international revenue by approximately 3% in Q4. 
Competition in the cloud market remains intense, with pricing pressure 
from major competitors. The company is investing heavily in AI capabilities, 
with R&D spending up 18% year-over-year.

Customer retention rate remained strong at 95%, and net revenue retention 
reached 115%, indicating existing customers are expanding their usage. 
The sales pipeline grew 20% quarter-over-quarter, suggesting continued 
momentum into the next fiscal year.
"""

CONTEXT_QUERY = "Summarize the key financial highlights and risks from this earnings report."

# =============================================================================
# Test Data: ReAct Agent
# =============================================================================

REACT_QUERIES = [
    "What is the population of Tokyo and how does it compare to New York?",
    "Calculate the compound interest on $10,000 at 5% for 10 years, then find the current inflation rate.",
    "Who won the last FIFA World Cup and in what year was it held?",
    "What is the distance from Earth to Mars, and how long would it take to travel there?",
    "Find the GDP of Germany and compare it to France's GDP.",
    "What is the boiling point of water at sea level in both Celsius and Fahrenheit?",
    "Who wrote 'Pride and Prejudice' and when was it published?",
    "Calculate the area of a circle with radius 7, then find the circumference.",
    "What is the capital of Australia and what is its population?",
    "How many days are in a leap year and when is the next one?",
]

# =============================================================================
# Test Data: Multi-Turn Conversation
# =============================================================================

CONVERSATION_STARTERS = [
    "I'm planning a trip to Japan. What should I know before going?",
    "Can you explain machine learning to me?",
    "I want to start investing in stocks. Where do I begin?",
    "Tell me about the history of the internet.",
    "I'm learning to cook. What are some essential skills?",
]

CONVERSATION_FOLLOWUPS = [
    ["Can you elaborate on that?", "What are the most important things to remember?", "Any common mistakes to avoid?", "How should I prepare?"],
    ["Can you give me a specific example?", "How is this used in practice?", "What are the limitations?", "Where can I learn more?"],
    ["What about the risks?", "How much money do I need to start?", "What's the difference between stocks and bonds?", "Any resources you recommend?"],
    ["What were the key milestones?", "Who were the main contributors?", "How has it changed over time?", "What's next for the internet?"],
    ["What equipment do I need?", "What recipes should I start with?", "How do I know if something is cooked properly?", "Any tips for meal planning?"],
]

# =============================================================================
# Test Data: Self-Correcting Code
# =============================================================================

CODE_TASKS = [
    "Write a Python function to check if a string is a palindrome.",
    "Create a function that finds the nth Fibonacci number.",
    "Write a function to reverse a linked list.",
    "Implement a binary search algorithm.",
    "Create a function that validates an email address.",
    "Write a function to merge two sorted arrays.",
    "Implement a function to detect cycles in a linked list.",
    "Create a function that converts Roman numerals to integers.",
    "Write a function to find all prime numbers up to n.",
    "Implement a simple LRU cache.",
]

CODE_VALIDATION_CRITERIA = """
1. The code should be syntactically correct Python
2. The function should handle edge cases (empty input, single element, etc.)
3. The code should be readable with clear variable names
4. The solution should be reasonably efficient
"""

# =============================================================================
# Test Data: Technical Document Analysis
# =============================================================================

TECHNICAL_DOCUMENTS = [
    # Document 1: Python code with bugs
    {
        "title": "User Authentication Module",
        "type": "code",
        "content": '''
import hashlib
import sqlite3

class UserAuth:
    def __init__(self):
        self.conn = sqlite3.connect('users.db')
        self.cursor = self.conn.cursor()
    
    def create_user(self, username, password):
        # Store password directly
        query = f"INSERT INTO users (username, password) VALUES ('{username}', '{password}')"
        self.cursor.execute(query)
        self.conn.commit()
        return True
    
    def login(self, username, password):
        query = f"SELECT * FROM users WHERE username='{username}' AND password='{password}'"
        result = self.cursor.execute(query)
        if result.fetchone():
            return True
        return False
    
    def delete_user(self, username):
        query = f"DELETE FROM users WHERE username='{username}'"
        self.cursor.execute(query)
        # Missing commit
        return True
    
    def get_all_users(self):
        self.cursor.execute("SELECT username, password FROM users")
        return self.cursor.fetchall()  # Exposing passwords
''',
        "expected_issues": ["SQL injection", "plaintext passwords", "missing commit", "password exposure"]
    },
    
    # Document 2: Kubernetes config with issues
    {
        "title": "Production Kubernetes Deployment",
        "type": "config",
        "content": '''
apiVersion: apps/v1
kind: Deployment
metadata:
  name: web-app
  namespace: default
spec:
  replicas: 1
  selector:
    matchLabels:
      app: web-app
  template:
    metadata:
      labels:
        app: web-app
    spec:
      containers:
      - name: web-app
        image: myapp:latest
        ports:
        - containerPort: 8080
        env:
        - name: DATABASE_PASSWORD
          value: "admin123"
        - name: API_KEY
          value: "sk-1234567890abcdef"
        securityContext:
          privileged: true
          runAsUser: 0
        resources: {}
---
apiVersion: v1
kind: Service
metadata:
  name: web-app
spec:
  type: LoadBalancer
  ports:
  - port: 8080
    targetPort: 8080
  selector:
    app: web-app
''',
        "expected_issues": ["hardcoded secrets", "privileged container", "running as root", "no resource limits", "latest tag", "single replica"]
    },
    
    # Document 3: API endpoint code with issues
    {
        "title": "REST API Endpoint Handler",
        "type": "code",
        "content": '''
from flask import Flask, request, jsonify
import os
import subprocess

app = Flask(__name__)

@app.route('/api/users/<user_id>', methods=['GET'])
def get_user(user_id):
    # No authentication check
    query = f"SELECT * FROM users WHERE id = {user_id}"
    result = db.execute(query)
    return jsonify(result)

@app.route('/api/execute', methods=['POST'])
def execute_command():
    cmd = request.json.get('command')
    # Direct command execution
    output = subprocess.check_output(cmd, shell=True)
    return jsonify({"output": output.decode()})

@app.route('/api/files', methods=['GET'])
def get_file():
    filename = request.args.get('path')
    # Path traversal vulnerability
    with open(filename, 'r') as f:
        return f.read()

@app.route('/api/upload', methods=['POST'])
def upload():
    file = request.files['file']
    # No file type validation
    file.save(f"/uploads/{file.filename}")
    return jsonify({"status": "uploaded"})

@app.errorhandler(Exception)
def handle_error(e):
    # Exposing internal errors
    return jsonify({"error": str(e), "traceback": traceback.format_exc()}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
''',
        "expected_issues": ["no authentication", "SQL injection", "command injection", "path traversal", "unrestricted file upload", "debug mode", "error exposure"]
    },
    
    # Document 4: Architecture document with issues
    {
        "title": "Microservices Architecture Design",
        "type": "architecture",
        "content": '''
# Payment Processing System Architecture

## Overview
Our payment system processes credit card transactions for our e-commerce platform.

## Components

### API Gateway
- Single instance running on EC2
- Handles all incoming traffic
- No rate limiting implemented
- HTTP only (TLS termination planned for Q3)

### Payment Service
- Processes transactions synchronously
- Stores full credit card numbers in PostgreSQL for easy refunds
- Logs all requests including card details for debugging
- Single database instance, no replication

### Notification Service
- Sends emails via SMTP
- Stores email credentials in environment variables
- No retry mechanism for failed sends

## Data Flow
1. User submits payment → API Gateway
2. API Gateway → Payment Service (HTTP)
3. Payment Service → Bank API (HTTPS)
4. Payment Service → Database (stores card data)
5. Payment Service → Notification Service

## Security
- Admin panel accessible at /admin with default credentials admin/admin
- API keys rotated annually
- No audit logging implemented yet

## Deployment
- Manual deployments via SSH
- No staging environment
- Rollback procedure: restore from last week's backup
''',
        "expected_issues": ["single point of failure", "no TLS", "PCI compliance violation", "storing card numbers", "logging sensitive data", "no rate limiting", "default credentials", "no audit logging"]
    },
    
    # Document 5: Terraform config with issues
    {
        "title": "AWS Infrastructure Terraform",
        "type": "config",
        "content": '''
provider "aws" {
  region     = "us-east-1"
  access_key = "AKIAIOSFODNN7EXAMPLE"
  secret_key = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
}

resource "aws_security_group" "web" {
  name = "web-sg"
  
  ingress {
    from_port   = 0
    to_port     = 65535
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
  
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_instance" "web" {
  ami           = "ami-12345678"
  instance_type = "t2.micro"
  
  vpc_security_group_ids = [aws_security_group.web.id]
  
  user_data = <<-EOF
              #!/bin/bash
              echo "DB_PASSWORD=supersecret123" >> /etc/environment
              EOF
  
  tags = {
    Name = "production-web"
  }
}

resource "aws_s3_bucket" "data" {
  bucket = "company-sensitive-data"
  acl    = "public-read"
}

resource "aws_db_instance" "main" {
  identifier     = "production-db"
  engine         = "mysql"
  instance_class = "db.t2.micro"
  username       = "admin"
  password       = "password123"
  
  publicly_accessible = true
  skip_final_snapshot = true
}
''',
        "expected_issues": ["hardcoded AWS credentials", "overly permissive security group", "public S3 bucket", "public RDS", "weak DB password", "secrets in user_data", "no encryption"]
    },
]

DOCUMENT_ANALYSIS_QUERY = "Analyze this technical document for potential security vulnerabilities, bugs, misconfigurations, or architectural issues. Identify and explain each issue found."

# =============================================================================
# Helper Functions
# =============================================================================

def get_model_id(model: str) -> str:
    """Resolve model alias to full model ID."""
    return MODEL_IDS.get(model, model)


def get_pricing(model: str) -> dict:
    """Get pricing for a model."""
    model_key = model if model in MODEL_PRICING else get_model_id(model)
    if model_key not in MODEL_PRICING:
        raise ValueError(f"Unknown model: {model}")
    return MODEL_PRICING[model_key]


def get_workflow_pipelines(workflow: str) -> list[str]:
    """Get list of pipeline names for a workflow."""
    if workflow not in WORKFLOWS:
        raise ValueError(f"Unknown workflow: {workflow}")
    return WORKFLOWS[workflow]["pipelines"]
