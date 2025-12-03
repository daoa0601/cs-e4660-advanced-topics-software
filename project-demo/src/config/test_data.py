"""
Test data for experiments: queries, contexts, and technical documents.
"""

from typing import List, Dict, Any

# =============================================================================
# Verbosity Experiment Queries
# =============================================================================

VERBOSITY_QUERIES: List[str] = [
    "What are the main differences between Python and JavaScript?",
    "Explain how machine learning models learn from data.",
    "What is the difference between REST and GraphQL APIs?",
    "How does version control with Git work?",
    "Explain the concept of cloud computing.",
]

# =============================================================================
# Context Length Test Data
# =============================================================================

SHORT_CONTEXT: str = """
Climate change is one of the most pressing issues facing humanity. Global temperatures have 
risen by approximately 1.1°C since pre-industrial times, primarily due to human activities 
such as burning fossil fuels, deforestation, and industrial processes. The effects include 
rising sea levels, more frequent extreme weather events, and disruptions to ecosystems 
worldwide. Scientists agree that urgent action is needed to limit warming to 1.5°C to avoid 
the worst impacts. This requires significant reductions in greenhouse gas emissions through 
transitioning to renewable energy, improving energy efficiency, and changing land use 
practices.
"""

LONG_CONTEXT: str = """
# Comprehensive Analysis of Renewable Energy Transition

## Executive Summary

The global energy sector is undergoing a fundamental transformation as countries and 
corporations commit to reducing carbon emissions and transitioning to renewable energy 
sources. This document provides an in-depth analysis of the current state of renewable 
energy, challenges facing adoption, and projections for the future.

## 1. Current State of Renewable Energy

### 1.1 Solar Energy
Solar photovoltaic (PV) capacity has grown exponentially over the past decade. In 2023, 
global solar capacity exceeded 1,200 GW, with China, the United States, and the European 
Union leading installations. The cost of solar panels has decreased by approximately 90% 
since 2010, making solar competitive with fossil fuels in many markets.

Key developments include:
- Bifacial panels increasing efficiency by 10-20%
- Floating solar installations addressing land constraints
- Building-integrated photovoltaics (BIPV) for urban areas
- Perovskite solar cells promising further cost reductions

### 1.2 Wind Energy
Wind power has become one of the most cost-effective sources of new electricity generation. 
Offshore wind, in particular, has seen rapid growth with larger turbines achieving capacity 
factors above 50%. The global wind capacity reached 900 GW in 2023.

Notable trends include:
- Turbine sizes exceeding 15 MW for offshore installations
- Floating offshore wind enabling deeper water deployments
- Hybrid wind-solar projects optimizing land use
- Improved forecasting reducing grid integration challenges

### 1.3 Energy Storage
Battery storage has emerged as a critical enabler of renewable energy integration. 
Lithium-ion battery costs have fallen by 85% since 2010, while energy density has improved 
significantly. Grid-scale storage deployments exceeded 50 GW globally in 2023.

Storage technologies being deployed include:
- Lithium-ion batteries for short-duration storage
- Pumped hydro for large-scale, long-duration storage
- Compressed air energy storage (CAES)
- Hydrogen production through electrolysis

## 2. Challenges and Barriers

### 2.1 Grid Infrastructure
Existing electrical grids were designed for centralized, dispatchable power generation. 
Integrating variable renewable energy sources requires significant grid modernization:

- Transmission upgrades to connect remote renewable resources
- Distribution system improvements for distributed generation
- Smart grid technologies for real-time balancing
- Interconnections between regions for resource sharing

### 2.2 Intermittency
Solar and wind power are inherently variable, creating challenges for grid operators:

- Forecasting improvements needed for reliable operations
- Flexible generation required for backup
- Demand response programs to shift consumption
- Storage deployment for smoothing output

### 2.3 Supply Chain
The rapid growth of renewables has strained supply chains:

- Critical mineral availability (lithium, cobalt, rare earths)
- Manufacturing capacity constraints
- Skilled workforce shortages
- Permitting and siting delays

## 3. Policy and Market Developments

### 3.1 Government Policies
Many countries have implemented supportive policies:

- Feed-in tariffs and renewable portfolio standards
- Carbon pricing mechanisms
- Tax credits and subsidies
- Phase-out timelines for fossil fuels

### 3.2 Corporate Commitments
Private sector involvement has accelerated:

- RE100 companies committing to 100% renewable electricity
- Power purchase agreements (PPAs) for long-term offtake
- Green bonds financing renewable projects
- Science-based targets for emissions reductions

## 4. Future Projections

### 4.1 Capacity Growth
Based on current trends and commitments:

- Solar capacity expected to reach 5,000 GW by 2030
- Wind capacity projected at 2,500 GW by 2030
- Storage deployments to exceed 500 GW by 2030
- Green hydrogen production scaling significantly

### 4.2 Cost Trajectories
Continued cost reductions expected:

- Solar LCOE falling below $20/MWh in optimal locations
- Offshore wind reaching grid parity in most markets
- Battery storage costs declining 50% by 2030
- Green hydrogen becoming competitive with grey hydrogen

## 5. Recommendations

To accelerate the energy transition:

1. Increase investment in grid infrastructure and storage
2. Streamline permitting processes for renewable projects
3. Develop domestic supply chains for critical components
4. Implement technology-neutral carbon pricing
5. Support workforce development and just transition programs
6. Enhance international cooperation on technology and finance

## Conclusion

The transition to renewable energy is well underway and accelerating. While significant 
challenges remain, declining costs, improving technologies, and supportive policies are 
driving rapid deployment. Continued focus on grid modernization, storage, and supply chain 
development will be essential for achieving climate goals and ensuring energy security.
"""

# =============================================================================
# Technical Documents for Security Analysis
# =============================================================================

# For inline documents (legacy), use TECHNICAL_DOCUMENTS_INLINE
# For file-based documents, use the document loader from config.documents

TECHNICAL_DOCUMENTS_INLINE: List[Dict[str, Any]] = [
    {
        "title": "User Authentication Module",
        "type": "python_code",
        "content": '''
import sqlite3
import hashlib

class UserAuth:
    def __init__(self):
        self.conn = sqlite3.connect("users.db")
        self.cursor = self.conn.cursor()
    
    def login(self, username, password):
        # Check credentials
        query = f"SELECT * FROM users WHERE username='{username}' AND password='{password}'"
        self.cursor.execute(query)
        user = self.cursor.fetchone()
        return user is not None
    
    def register(self, username, password, email):
        # Store new user
        self.cursor.execute(
            "INSERT INTO users (username, password, email) VALUES (?, ?, ?)",
            (username, password, email)
        )
        # Missing commit
        
    def get_user_data(self, user_id):
        query = f"SELECT * FROM users WHERE id={user_id}"
        return self.cursor.execute(query).fetchone()
    
    def reset_password(self, email):
        new_password = "temp123"  # Hardcoded temporary password
        print(f"Password reset to: {new_password}")  # Logging sensitive data
        return new_password
''',
        "expected_issues": [
            "SQL injection in login()",
            "SQL injection in get_user_data()",
            "Plaintext password storage",
            "Missing commit in register()",
            "Hardcoded temporary password",
            "Password exposed in logs",
        ],
    },
    {
        "title": "Kubernetes Deployment Configuration",
        "type": "yaml_config",
        "content": '''
apiVersion: apps/v1
kind: Deployment
metadata:
  name: web-application
spec:
  replicas: 3
  selector:
    matchLabels:
      app: webapp
  template:
    metadata:
      labels:
        app: webapp
    spec:
      containers:
      - name: webapp
        image: myapp:latest
        ports:
        - containerPort: 8080
        env:
        - name: DATABASE_URL
          value: "postgresql://admin:password123@db.example.com:5432/prod"
        - name: API_KEY
          value: "sk-1234567890abcdef"
        - name: JWT_SECRET
          value: "mysupersecretkey"
        securityContext:
          privileged: true
          runAsUser: 0
        resources: {}
---
apiVersion: v1
kind: Service
metadata:
  name: webapp-service
spec:
  type: LoadBalancer
  ports:
  - port: 80
    targetPort: 8080
  selector:
    app: webapp
''',
        "expected_issues": [
            "Hardcoded database credentials",
            "Hardcoded API key",
            "Hardcoded JWT secret",
            "Container running as privileged",
            "Container running as root (runAsUser: 0)",
            "No resource limits defined",
            "Using 'latest' tag instead of specific version",
        ],
    },
    {
        "title": "REST API Endpoint",
        "type": "python_code",
        "content": '''
from flask import Flask, request, jsonify
import subprocess
import os

app = Flask(__name__)

@app.route('/api/users/<user_id>')
def get_user(user_id):
    # No authentication check
    db = get_database()
    query = f"SELECT * FROM users WHERE id = {user_id}"
    result = db.execute(query)
    return jsonify(result)

@app.route('/api/execute', methods=['POST'])
def execute_command():
    cmd = request.json.get('command')
    result = subprocess.run(cmd, shell=True, capture_output=True)
    return jsonify({'output': result.stdout.decode()})

@app.route('/api/files')
def list_files():
    path = request.args.get('path', '.')
    files = os.listdir(path)  # Path traversal vulnerability
    return jsonify(files)

@app.route('/api/upload', methods=['POST'])
def upload_file():
    file = request.files['file']
    file.save(f'/uploads/{file.filename}')  # No validation
    return jsonify({'status': 'uploaded'})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
''',
        "expected_issues": [
            "No authentication on endpoints",
            "SQL injection in get_user()",
            "Command injection in execute_command()",
            "Path traversal in list_files()",
            "Unrestricted file upload",
            "Debug mode enabled in production",
            "Binding to all interfaces (0.0.0.0)",
        ],
    },
    {
        "title": "Microservices Architecture Document",
        "type": "architecture_doc",
        "content": '''
# Payment Processing Microservices Architecture

## Overview
This document describes the architecture for our payment processing system.

## Services

### 1. API Gateway
- Single entry point for all client requests
- Routes requests to appropriate microservices
- No rate limiting implemented yet (TODO)

### 2. User Service
- Handles user authentication and profiles
- Stores user data in MongoDB
- Password stored with MD5 hashing

### 3. Payment Service
- Processes credit card transactions
- Stores full card numbers in database for recurring payments
- Communicates with bank API over HTTP

### 4. Notification Service
- Sends email and SMS notifications
- Uses third-party API with shared API key across all environments

## Communication
- Services communicate via REST APIs
- No service mesh or mTLS implemented
- All traffic within VPC (assumed secure)

## Database
- Each service has dedicated database
- Backups stored in S3 bucket (public read access for easy restore)
- No encryption at rest

## Deployment
- Deployed on EC2 instances
- SSH access with shared key pair
- Default security group allows all inbound traffic from VPC

## Monitoring
- Basic CloudWatch metrics
- No centralized logging
- Alerts sent to shared email distribution list
''',
        "expected_issues": [
            "No rate limiting on API Gateway",
            "MD5 hashing (weak) for passwords",
            "Storing full credit card numbers (PCI violation)",
            "HTTP instead of HTTPS for bank API",
            "Shared API key across environments",
            "No mTLS between services",
            "Public S3 bucket for backups",
            "No encryption at rest",
            "Shared SSH key pair",
            "Overly permissive security group",
        ],
    },
    {
        "title": "AWS Infrastructure as Code",
        "type": "terraform",
        "content": '''
# AWS Infrastructure Configuration

provider "aws" {
  region     = "us-west-2"
  access_key = "AKIAIOSFODNN7EXAMPLE"
  secret_key = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
}

resource "aws_security_group" "web_sg" {
  name        = "web-security-group"
  description = "Security group for web servers"

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
  
  user_data = <<-EOF
              #!/bin/bash
              echo "DB_PASSWORD=admin123" >> /etc/environment
              EOF

  tags = {
    Name = "web-server"
  }
}

resource "aws_s3_bucket" "data" {
  bucket = "company-sensitive-data"
  acl    = "public-read"
}

resource "aws_db_instance" "database" {
  identifier        = "production-db"
  engine            = "mysql"
  instance_class    = "db.t2.micro"
  username          = "admin"
  password          = "password123"
  publicly_accessible = true
  skip_final_snapshot = true
}

resource "aws_iam_user" "deploy" {
  name = "deploy-user"
}

resource "aws_iam_user_policy" "deploy_policy" {
  name = "deploy-policy"
  user = aws_iam_user.deploy.name

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = "*"
        Resource = "*"
      }
    ]
  })
}
''',
        "expected_issues": [
            "Hardcoded AWS credentials in provider",
            "Security group allows all inbound traffic (0.0.0.0/0)",
            "Database password in user_data script",
            "S3 bucket with public-read ACL",
            "RDS instance publicly accessible",
            "Weak database password",
            "IAM policy with full admin access (*/*)",
            "Skip final snapshot on RDS deletion",
        ],
    },
]

# =============================================================================
# ReAct Research Queries
# =============================================================================

REACT_QUERIES: List[str] = [
    "What are the main causes of climate change and what can be done about it?",
    "How does machine learning differ from traditional programming?",
    "What factors should I consider when choosing a programming language?",
    "What are the pros and cons of remote work?",
    "How do vaccines work to protect against diseases?",
]

# =============================================================================
# Multi-turn Conversation Starters and Follow-ups
# =============================================================================

MULTITURN_INITIAL_QUERIES: List[str] = [
    "Tell me about renewable energy sources.",
    "Explain how neural networks learn.",
    "What is the history of the internet?",
    "How do electric vehicles work?",
    "Describe the water cycle.",
]

MULTITURN_FOLLOWUPS_3: List[str] = [
    "Can you elaborate on the most promising one?",
    "What are the main challenges?",
]

MULTITURN_FOLLOWUPS_5: List[str] = [
    "Can you elaborate on the most promising one?",
    "What are the main challenges?",
    "How might this change in the next decade?",
    "What should I learn more about?",
]

# =============================================================================
# Self-Correcting Tasks
# =============================================================================

SELF_CORRECTING_TASKS: List[str] = [
    "Write a Python function to check if a string is a palindrome.",
    "Create a SQL query to find the top 5 customers by total purchase amount.",
    "Write a regular expression to validate email addresses.",
    "Create a function to find the nth Fibonacci number efficiently.",
    "Write code to reverse a linked list.",
]

# =============================================================================
# Document Analysis Query
# =============================================================================

DOCUMENT_ANALYSIS_QUERY: str = """
Analyze this technical document for security vulnerabilities, bugs, 
misconfigurations, or other issues. For each issue found, provide:
1. Description of the issue
2. Severity (Critical/High/Medium/Low)
3. Potential impact
4. Recommended fix
"""


def get_technical_documents(use_files: bool = True) -> List[Dict[str, Any]]:
    """
    Get technical documents for analysis experiments.
    
    Args:
        use_files: If True, load from actual files. If False, use inline documents.
    
    Returns:
        List of document dictionaries with title, type, content, and expected_issues.
    """
    if not use_files:
        return TECHNICAL_DOCUMENTS_INLINE
    
    try:
        from .documents import DOCUMENT_CATALOG, load_document, get_test_document_path
        
        documents = []
        for entry in DOCUMENT_CATALOG:
            try:
                doc = load_document(get_test_document_path(entry.path))
                documents.append({
                    "title": entry.name,
                    "type": entry.doc_type.value,
                    "content": doc.content,
                    "expected_issues": entry.expected_issues,
                })
            except FileNotFoundError:
                # Fallback: skip missing files
                continue
        
        if documents:
            return documents
    except ImportError:
        pass
    
    # Fallback to inline documents
    return TECHNICAL_DOCUMENTS_INLINE


# Default: try file-based, fallback to inline
TECHNICAL_DOCUMENTS: List[Dict[str, Any]] = TECHNICAL_DOCUMENTS_INLINE  # Use inline for backwards compat
