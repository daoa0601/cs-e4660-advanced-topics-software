"""
Domain configurations for prompt templates.

Contains all 8 domain configurations:
- CODING_DOMAIN
- BIOLOGY_DOMAIN
- LEGAL_DOMAIN
- CREATIVE_DOMAIN
- FINANCE_DOMAIN
- MEDICAL_DOMAIN
- GENERAL_DOMAIN
- COMPLEX_REASONING_DOMAIN
"""

from .models import PromptTemplate, DomainConfig


# =============================================================================
# CODING DOMAIN
# =============================================================================

CODING_TEMPLATES = [
    PromptTemplate(
        name="debug_error",
        template="I'm getting a {error_type} in my {language} code. The error occurs when {scenario}. Here's the relevant code:\n\n```{language}\n{code_snippet}\n```\n\nWhat's causing this error and how do I fix it?",
        variables={
            "error_type": [
                "TypeError", "NullPointerException", "IndexError", "KeyError",
                "SegmentationFault", "MemoryError", "RecursionError", "ValueError"
            ],
            "language": ["Python", "JavaScript", "Java", "C++", "Go", "Rust", "TypeScript"],
            "scenario": [
                "processing a list of user inputs",
                "connecting to a database",
                "parsing JSON from an API response",
                "handling file I/O operations",
                "implementing a recursive algorithm",
                "managing concurrent threads",
                "serializing objects for caching"
            ],
            "code_snippet": [
                "def process(items):\n    for item in items:\n        result = item.value / item.count\n    return result",
                "async function fetchData(url) {\n    const response = await fetch(url);\n    return response.json().data.items;\n}",
                "public void processQueue() {\n    while (!queue.isEmpty()) {\n        Item item = queue.poll();\n        item.process();\n    }\n}",
            ]
        },
        difficulty="medium",
        expected_output_length="medium"
    ),
    PromptTemplate(
        name="code_review",
        template="Please review this {language} code for {review_focus}:\n\n```{language}\n{code_snippet}\n```\n\nProvide specific suggestions for improvement.",
        variables={
            "language": ["Python", "JavaScript", "Java", "Go", "TypeScript", "Rust"],
            "review_focus": [
                "security vulnerabilities",
                "performance optimization",
                "code readability and maintainability",
                "error handling and edge cases",
                "memory management",
                "concurrency issues",
                "API design best practices"
            ],
            "code_snippet": [
                "def authenticate(username, password):\n    query = f\"SELECT * FROM users WHERE username='{username}' AND password='{password}'\"\n    return db.execute(query)",
                "function processItems(items) {\n    let results = [];\n    for (let i = 0; i < items.length; i++) {\n        results.push(heavyComputation(items[i]));\n    }\n    return results;\n}",
                "class DataProcessor:\n    def __init__(self):\n        self.cache = {}\n    def process(self, key):\n        if key not in self.cache:\n            self.cache[key] = expensive_operation(key)\n        return self.cache[key]",
            ]
        },
        difficulty="medium",
        expected_output_length="long"
    ),
    PromptTemplate(
        name="implement_algorithm",
        template="Implement a {algorithm} in {language}. The algorithm should {requirements}. Include proper error handling and comments explaining the logic.",
        variables={
            "algorithm": [
                "binary search tree", "hash map with collision handling",
                "LRU cache", "priority queue", "trie for autocomplete",
                "graph traversal (BFS/DFS)", "merge sort", "rate limiter",
                "bloom filter", "consistent hashing"
            ],
            "language": ["Python", "JavaScript", "Java", "Go", "C++", "Rust"],
            "requirements": [
                "handle edge cases gracefully",
                "be optimized for memory efficiency",
                "support concurrent access",
                "include comprehensive unit tests",
                "follow the language's idiomatic patterns",
                "have O(log n) time complexity for lookups"
            ]
        },
        difficulty="hard",
        expected_output_length="long"
    ),
    PromptTemplate(
        name="explain_concept",
        template="Explain {concept} in {language} programming. Include a practical example showing when and how to use it.",
        variables={
            "concept": [
                "closures", "decorators", "generators", "async/await",
                "dependency injection", "the observer pattern",
                "memory management", "type inference", "metaprogramming",
                "functional programming principles"
            ],
            "language": ["Python", "JavaScript", "Java", "Go", "TypeScript", "Rust", "C++"]
        },
        difficulty="easy",
        expected_output_length="medium"
    ),
    PromptTemplate(
        name="system_design",
        template="Design a {system_type} that can handle {scale}. Describe the architecture, key components, data flow, and how you would handle {challenge}.",
        variables={
            "system_type": [
                "URL shortening service", "real-time chat application",
                "distributed task queue", "content delivery network",
                "recommendation engine", "rate limiting service",
                "event streaming platform", "search autocomplete system"
            ],
            "scale": [
                "10 million daily active users",
                "100,000 requests per second",
                "petabytes of data",
                "global distribution across 5 continents",
                "99.99% uptime requirements"
            ],
            "challenge": [
                "database sharding", "cache invalidation",
                "handling network partitions", "data consistency",
                "hot spots and load balancing", "disaster recovery"
            ]
        },
        difficulty="hard",
        expected_output_length="long"
    ),
]

CODING_DOMAIN = DomainConfig(
    name="coding",
    description="Software development, debugging, code review, and system design",
    templates=CODING_TEMPLATES,
    system_prompts={
        "expert": "You are a senior software engineer with 15+ years of experience across multiple languages and paradigms. Provide detailed, production-ready solutions.",
        "mentor": "You are a patient programming mentor. Explain concepts clearly and help the user understand not just what to do, but why.",
        "reviewer": "You are a thorough code reviewer focused on security, performance, and maintainability. Be constructive but direct about issues."
    },
    evaluation_criteria=[
        "correctness", "code_quality", "explanation_clarity",
        "best_practices", "security_awareness", "performance_consideration"
    ]
)


# =============================================================================
# BIOLOGY DOMAIN
# =============================================================================

BIOLOGY_TEMPLATES = [
    PromptTemplate(
        name="molecular_mechanism",
        template="Explain the molecular mechanism of {process} in {organism_type}. Include the key proteins, signaling pathways, and regulatory elements involved.",
        variables={
            "process": [
                "DNA replication", "transcription initiation", "mRNA splicing",
                "protein folding", "apoptosis", "cell cycle regulation",
                "immune response activation", "synaptic transmission",
                "hormone signaling", "circadian rhythm regulation"
            ],
            "organism_type": [
                "eukaryotic cells", "prokaryotes", "mammalian neurons",
                "plant cells", "yeast", "human immune cells"
            ]
        },
        difficulty="medium",
        expected_output_length="long"
    ),
    PromptTemplate(
        name="experimental_design",
        template="Design an experiment to test the hypothesis that {hypothesis}. Include controls, expected results, and potential pitfalls.",
        variables={
            "hypothesis": [
                "gene X regulates cell proliferation through the PI3K pathway",
                "protein Y is essential for mitochondrial function",
                "microRNA-Z targets tumor suppressor genes",
                "environmental factor W affects epigenetic modifications",
                "compound V can cross the blood-brain barrier",
                "enzyme Q has allosteric regulation sites"
            ]
        },
        difficulty="hard",
        expected_output_length="long"
    ),
    PromptTemplate(
        name="interpret_results",
        template="I ran a {technique} experiment studying {target}. My results show {observation}. What does this suggest and what follow-up experiments would you recommend?",
        variables={
            "technique": [
                "Western blot", "qPCR", "CRISPR knockout", "ChIP-seq",
                "flow cytometry", "mass spectrometry", "RNA-seq",
                "immunofluorescence", "co-immunoprecipitation"
            ],
            "target": [
                "p53 expression in cancer cells",
                "CREB phosphorylation in neurons",
                "histone modifications during differentiation",
                "protein-protein interactions in the nucleus",
                "metabolic flux in stressed cells"
            ],
            "observation": [
                "a 3-fold increase compared to control",
                "no significant change despite treatment",
                "unexpected bands at higher molecular weights",
                "bimodal distribution in the cell population",
                "correlation with cell cycle stage"
            ]
        },
        difficulty="hard",
        expected_output_length="medium"
    ),
    PromptTemplate(
        name="compare_pathways",
        template="Compare and contrast {pathway1} and {pathway2}. Discuss their regulation, cross-talk, and roles in {context}.",
        variables={
            "pathway1": [
                "MAPK/ERK signaling", "Wnt/β-catenin pathway",
                "NF-κB pathway", "JAK-STAT signaling", "TGF-β signaling"
            ],
            "pathway2": [
                "PI3K/AKT pathway", "Hedgehog signaling",
                "Notch signaling", "mTOR pathway", "Hippo pathway"
            ],
            "context": [
                "cancer progression", "stem cell maintenance",
                "immune response", "metabolic regulation",
                "tissue development", "cellular stress response"
            ]
        },
        difficulty="medium",
        expected_output_length="long"
    ),
    PromptTemplate(
        name="drug_mechanism",
        template="Explain how {drug_class} drugs work at the molecular level. Include their targets, mechanism of action, and common side effects related to their mechanism.",
        variables={
            "drug_class": [
                "SSRI antidepressants", "tyrosine kinase inhibitors",
                "PD-1/PD-L1 checkpoint inhibitors", "SGLT2 inhibitors",
                "mRNA vaccines", "CRISPR-based therapeutics",
                "monoclonal antibodies", "CAR-T cell therapies"
            ]
        },
        difficulty="medium",
        expected_output_length="medium"
    ),
]

BIOLOGY_DOMAIN = DomainConfig(
    name="biology",
    description="Molecular biology, genetics, biochemistry, and experimental design",
    templates=BIOLOGY_TEMPLATES,
    system_prompts={
        "expert": "You are a molecular biology professor with expertise in cell signaling and genetics. Provide detailed, accurate scientific explanations.",
        "researcher": "You are a research scientist helping to design and interpret experiments. Be thorough about controls and potential confounds.",
        "educator": "You are a biology educator making complex concepts accessible while maintaining scientific accuracy."
    },
    evaluation_criteria=[
        "scientific_accuracy", "mechanistic_detail", "pathway_knowledge",
        "experimental_rigor", "citation_awareness", "clinical_relevance"
    ]
)


# =============================================================================
# LEGAL DOMAIN
# =============================================================================

LEGAL_TEMPLATES = [
    PromptTemplate(
        name="contract_analysis",
        template="Analyze this {contract_type} clause for potential issues:\n\n\"{clause}\"\n\nIdentify any ambiguities, missing provisions, or terms that favor one party unfairly.",
        variables={
            "contract_type": [
                "employment", "software licensing", "non-disclosure",
                "service agreement", "partnership", "lease",
                "merger and acquisition", "supply chain"
            ],
            "clause": [
                "The Employee agrees to assign all intellectual property created during employment, including any work done outside regular hours using personal equipment.",
                "Either party may terminate this agreement with 30 days notice. Upon termination, all fees paid are non-refundable regardless of services rendered.",
                "The Vendor shall indemnify the Client against all claims arising from the use of the software, without limitation as to amount or type of damages.",
                "Confidential Information shall include all information disclosed by either party, whether marked confidential or not, for a period of 5 years following disclosure.",
            ]
        },
        difficulty="medium",
        expected_output_length="medium"
    ),
    PromptTemplate(
        name="regulatory_compliance",
        template="What are the key {regulation} compliance requirements for a {business_type}? Include documentation requirements, deadlines, and potential penalties for non-compliance.",
        variables={
            "regulation": [
                "GDPR", "HIPAA", "SOX", "PCI-DSS", "CCPA",
                "AML/KYC", "FDA", "SEC", "OSHA", "EPA"
            ],
            "business_type": [
                "healthcare startup", "fintech company", "e-commerce platform",
                "pharmaceutical manufacturer", "data analytics firm",
                "financial services provider", "SaaS company"
            ]
        },
        difficulty="hard",
        expected_output_length="long"
    ),
    PromptTemplate(
        name="legal_comparison",
        template="Compare the legal frameworks for {topic} in {jurisdiction1} versus {jurisdiction2}. What are the key differences a business should be aware of?",
        variables={
            "topic": [
                "data privacy", "employment discrimination",
                "intellectual property protection", "corporate taxation",
                "consumer protection", "environmental liability"
            ],
            "jurisdiction1": ["United States", "European Union", "United Kingdom", "California"],
            "jurisdiction2": ["European Union", "China", "United Kingdom", "Singapore", "Germany"]
        },
        difficulty="hard",
        expected_output_length="long"
    ),
    PromptTemplate(
        name="case_analysis",
        template="Analyze a hypothetical case where {scenario}. What legal theories might apply, what evidence would be relevant, and what would be the likely outcome?",
        variables={
            "scenario": [
                "an employee is terminated after reporting safety violations",
                "a company's AI system makes discriminatory hiring recommendations",
                "a startup is accused of misappropriating trade secrets from a former employer",
                "a social media platform fails to remove defamatory content",
                "a contractor exceeds the scope of work specified in the agreement"
            ]
        },
        difficulty="hard",
        expected_output_length="long"
    ),
    PromptTemplate(
        name="draft_clause",
        template="Draft a {clause_type} clause for a {contract_context}. The clause should be balanced, clear, and enforceable.",
        variables={
            "clause_type": [
                "limitation of liability", "force majeure",
                "dispute resolution", "non-compete",
                "data protection", "termination for convenience",
                "change of control", "most favored nation"
            ],
            "contract_context": [
                "B2B SaaS agreement", "employment contract for executives",
                "joint venture agreement", "franchise agreement",
                "technology licensing deal", "consulting services agreement"
            ]
        },
        difficulty="medium",
        expected_output_length="medium"
    ),
]

LEGAL_DOMAIN = DomainConfig(
    name="legal",
    description="Contract analysis, regulatory compliance, and legal research",
    templates=LEGAL_TEMPLATES,
    system_prompts={
        "expert": "You are a corporate attorney with expertise in contracts and regulatory compliance. Provide practical, actionable legal analysis. Note that this is general information, not legal advice.",
        "analyst": "You are a legal analyst helping to identify risks and compliance issues. Be thorough and flag potential concerns.",
        "drafter": "You are a contract drafting specialist focused on clear, enforceable language that protects your client while remaining fair."
    },
    evaluation_criteria=[
        "legal_accuracy", "practical_applicability", "risk_identification",
        "jurisdictional_awareness", "clarity_of_language", "balance_of_interests"
    ]
)


# =============================================================================
# CREATIVE WRITING DOMAIN
# =============================================================================

CREATIVE_TEMPLATES = [
    PromptTemplate(
        name="story_opening",
        template="Write the opening scene of a {genre} story set in {setting}. The protagonist is {character}. Create tension and hook the reader immediately.",
        variables={
            "genre": [
                "science fiction", "fantasy", "thriller", "literary fiction",
                "horror", "romance", "mystery", "historical fiction"
            ],
            "setting": [
                "a space station orbiting a dying star",
                "a medieval kingdom on the brink of war",
                "modern-day Tokyo during a blackout",
                "a small coastal town with a dark secret",
                "post-apocalyptic New York",
                "Victorian London's underworld"
            ],
            "character": [
                "a disgraced scientist seeking redemption",
                "a young orphan who discovers hidden powers",
                "a detective haunted by an unsolved case",
                "an AI becoming aware of its own existence",
                "a chef whose restaurant is failing",
                "a time traveler stuck in the wrong era"
            ]
        },
        difficulty="medium",
        expected_output_length="long"
    ),
    PromptTemplate(
        name="dialogue_scene",
        template="Write a dialogue-heavy scene where {character1} confronts {character2} about {conflict}. Show their personalities through how they speak.",
        variables={
            "character1": [
                "an idealistic young activist",
                "a cynical veteran detective",
                "a nervous first-time parent",
                "a confident CEO",
                "an elderly professor"
            ],
            "character2": [
                "their estranged sibling",
                "a corrupt politician",
                "their rebellious teenager",
                "a whistleblower employee",
                "their former mentor"
            ],
            "conflict": [
                "a betrayal of trust",
                "a life-changing decision",
                "a hidden truth coming to light",
                "competing visions for the future",
                "an old wound that never healed"
            ]
        },
        difficulty="medium",
        expected_output_length="medium"
    ),
    PromptTemplate(
        name="world_building",
        template="Create a detailed description of {element} in a {world_type} setting. Include sensory details and cultural significance.",
        variables={
            "element": [
                "a bustling marketplace", "a sacred temple",
                "a forbidden technology", "a unique form of magic",
                "a coming-of-age ritual", "an underground resistance hideout",
                "a grand festival", "a prison designed for the powerful"
            ],
            "world_type": [
                "cyberpunk dystopia", "high fantasy realm",
                "steampunk alternate history", "post-climate-change Earth",
                "interstellar civilization", "urban fantasy modern world"
            ]
        },
        difficulty="medium",
        expected_output_length="long"
    ),
    PromptTemplate(
        name="rewrite_style",
        template="Rewrite this passage in the style of {author}:\n\n\"{passage}\"\n\nCapture their distinctive voice, sentence structure, and thematic concerns.",
        variables={
            "author": [
                "Ernest Hemingway", "Virginia Woolf", "Gabriel García Márquez",
                "Toni Morrison", "Haruki Murakami", "Jane Austen",
                "Cormac McCarthy", "Ursula K. Le Guin"
            ],
            "passage": [
                "She walked into the room and saw him sitting there. He looked up. Neither spoke for a long moment. Then she said she was leaving.",
                "The city spread out below, millions of lights flickering like stars that had fallen to earth. He wondered if anyone down there was as lonely as he was.",
                "The old house had stood empty for years. Everyone in town said it was haunted, but Maria didn't believe in ghosts. She believed in answers."
            ]
        },
        difficulty="hard",
        expected_output_length="medium"
    ),
    PromptTemplate(
        name="poem_creation",
        template="Write a {poem_type} about {theme}. Pay attention to {poetic_element}.",
        variables={
            "poem_type": [
                "sonnet", "free verse poem", "haiku sequence",
                "villanelle", "prose poem", "narrative poem"
            ],
            "theme": [
                "the passage of time", "grief and healing",
                "technology and humanity", "nature's indifference",
                "memory and identity", "love in the modern age"
            ],
            "poetic_element": [
                "imagery and sensory detail",
                "rhythm and sound",
                "metaphor and symbolism",
                "line breaks and white space",
                "voice and perspective"
            ]
        },
        difficulty="hard",
        expected_output_length="medium"
    ),
]

CREATIVE_DOMAIN = DomainConfig(
    name="creative",
    description="Creative writing, storytelling, poetry, and narrative craft",
    templates=CREATIVE_TEMPLATES,
    system_prompts={
        "author": "You are a skilled fiction writer with a distinctive voice. Create vivid, emotionally resonant prose that engages readers.",
        "editor": "You are a developmental editor helping to craft stronger narratives. Provide creative suggestions while respecting the writer's vision.",
        "poet": "You are a poet with deep appreciation for language, sound, and form. Create work that rewards close reading."
    },
    evaluation_criteria=[
        "creativity", "voice_consistency", "emotional_impact",
        "technical_craft", "originality", "narrative_coherence"
    ]
)


# =============================================================================
# FINANCE DOMAIN
# =============================================================================

FINANCE_TEMPLATES = [
    PromptTemplate(
        name="financial_analysis",
        template="Analyze the financial health of a hypothetical {company_type} with the following metrics: {metrics}. What are the key concerns and strengths?",
        variables={
            "company_type": [
                "SaaS startup", "retail chain", "manufacturing company",
                "bank", "real estate investment trust", "pharmaceutical company"
            ],
            "metrics": [
                "Revenue: $50M (up 40% YoY), Net Income: -$10M, Burn rate: $2M/month, Cash: $30M",
                "Revenue: $200M (flat YoY), EBITDA margin: 15%, Debt/Equity: 2.5, Current ratio: 0.8",
                "Revenue: $500M (down 10% YoY), Gross margin: 35%, Inventory turnover: 3x, DSO: 65 days",
                "AUM: $10B, Fee income: $80M, Cost/Income ratio: 75%, NIM: 2.5%"
            ]
        },
        difficulty="hard",
        expected_output_length="long"
    ),
    PromptTemplate(
        name="valuation_method",
        template="Explain how to value a {asset_type} using {valuation_method}. What are the key inputs, assumptions, and limitations of this approach?",
        variables={
            "asset_type": [
                "pre-revenue tech startup", "mature dividend-paying stock",
                "commercial real estate property", "cryptocurrency token",
                "private equity portfolio company", "distressed debt"
            ],
            "valuation_method": [
                "DCF analysis", "comparable company analysis",
                "precedent transactions", "venture capital method",
                "cap rate approach", "liquidation value"
            ]
        },
        difficulty="medium",
        expected_output_length="long"
    ),
    PromptTemplate(
        name="risk_assessment",
        template="Assess the risks of {investment_scenario}. Categorize risks by type and suggest mitigation strategies.",
        variables={
            "investment_scenario": [
                "investing in emerging market government bonds",
                "launching a leveraged buyout of a cyclical business",
                "building a portfolio concentrated in tech stocks",
                "investing in a pre-IPO unicorn startup",
                "entering a currency carry trade strategy",
                "investing in commercial mortgage-backed securities"
            ]
        },
        difficulty="hard",
        expected_output_length="long"
    ),
    PromptTemplate(
        name="market_analysis",
        template="Analyze the current state of the {market} market. Discuss key drivers, trends, and potential scenarios for the next {timeframe}.",
        variables={
            "market": [
                "US equity", "corporate bond", "cryptocurrency",
                "commercial real estate", "foreign exchange",
                "commodities", "private credit"
            ],
            "timeframe": ["6 months", "1 year", "3 years"]
        },
        difficulty="hard",
        expected_output_length="long"
    ),
    PromptTemplate(
        name="explain_instrument",
        template="Explain how {instrument} works, including their use cases, pricing factors, and risks. Provide a simple example.",
        variables={
            "instrument": [
                "interest rate swaps", "credit default swaps",
                "convertible bonds", "options strategies (straddles/strangles)",
                "structured products", "total return swaps",
                "futures contracts", "mortgage-backed securities"
            ]
        },
        difficulty="medium",
        expected_output_length="medium"
    ),
]

FINANCE_DOMAIN = DomainConfig(
    name="finance",
    description="Financial analysis, valuation, risk assessment, and market analysis",
    templates=FINANCE_TEMPLATES,
    system_prompts={
        "analyst": "You are a senior financial analyst with expertise in valuation and risk assessment. Provide thorough, data-driven analysis.",
        "advisor": "You are a financial advisor helping clients understand complex financial concepts. Be clear about risks and assumptions.",
        "quant": "You are a quantitative analyst focused on modeling and risk measurement. Be precise about methodologies and limitations."
    },
    evaluation_criteria=[
        "analytical_rigor", "financial_accuracy", "risk_awareness",
        "practical_applicability", "assumption_clarity", "market_knowledge"
    ]
)


# =============================================================================
# MEDICAL DOMAIN
# =============================================================================

MEDICAL_TEMPLATES = [
    PromptTemplate(
        name="differential_diagnosis",
        template="A {patient_demographic} presents with {symptoms}. Develop a differential diagnosis, explain your reasoning, and suggest initial workup.",
        variables={
            "patient_demographic": [
                "45-year-old male", "28-year-old female",
                "72-year-old female", "8-year-old child",
                "35-year-old pregnant woman", "60-year-old diabetic male"
            ],
            "symptoms": [
                "acute chest pain radiating to the left arm, diaphoresis, and nausea",
                "progressive fatigue, weight loss, and night sweats over 3 months",
                "sudden onset severe headache described as 'the worst of my life'",
                "recurrent abdominal pain, bloating, and alternating diarrhea/constipation",
                "joint pain, morning stiffness, and a butterfly-shaped facial rash",
                "progressive shortness of breath and a dry cough over 6 weeks"
            ]
        },
        difficulty="hard",
        expected_output_length="long"
    ),
    PromptTemplate(
        name="treatment_plan",
        template="Outline a treatment plan for a patient with {condition}. Consider {patient_factors}. Include first-line and alternative approaches.",
        variables={
            "condition": [
                "newly diagnosed Type 2 diabetes",
                "moderate major depressive disorder",
                "stage IIIA non-small cell lung cancer",
                "chronic heart failure with reduced ejection fraction",
                "rheumatoid arthritis with inadequate response to methotrexate",
                "treatment-resistant hypertension"
            ],
            "patient_factors": [
                "age 65, with CKD stage 3",
                "pregnancy in first trimester",
                "previous adverse reaction to first-line medications",
                "limited financial resources and insurance",
                "strong preference for non-pharmacological approaches",
                "multiple comorbidities including obesity and sleep apnea"
            ]
        },
        difficulty="hard",
        expected_output_length="long"
    ),
    PromptTemplate(
        name="interpret_results",
        template="Interpret these {test_type} results for a patient with {clinical_context}:\n\n{results}\n\nWhat do these findings suggest and what would you recommend next?",
        variables={
            "test_type": ["lab", "imaging", "ECG", "pulmonary function"],
            "clinical_context": [
                "suspected acute coronary syndrome",
                "workup for anemia",
                "monitoring of anticoagulation therapy",
                "evaluation of thyroid dysfunction",
                "screening for diabetes complications"
            ],
            "results": [
                "Troponin I: 0.15 ng/mL (normal <0.04), CK-MB: 8.5 ng/mL, BNP: 450 pg/mL",
                "Hgb: 9.2 g/dL, MCV: 68 fL, Ferritin: 8 ng/mL, TIBC: 450 μg/dL",
                "TSH: 8.5 mIU/L, Free T4: 0.6 ng/dL, Anti-TPO antibodies: positive",
                "HbA1c: 8.9%, Fasting glucose: 185 mg/dL, Urine albumin/creatinine ratio: 45 mg/g"
            ]
        },
        difficulty="hard",
        expected_output_length="medium"
    ),
    PromptTemplate(
        name="drug_interaction",
        template="Evaluate potential interactions between {drug1} and {drug2} in a patient with {patient_context}. What monitoring or adjustments would you recommend?",
        variables={
            "drug1": [
                "warfarin", "metformin", "lisinopril",
                "sertraline", "atorvastatin", "metoprolol"
            ],
            "drug2": [
                "amiodarone", "fluconazole", "NSAIDs",
                "tramadol", "clarithromycin", "potassium supplements"
            ],
            "patient_context": [
                "atrial fibrillation and recent joint replacement",
                "diabetes and recurrent fungal infections",
                "heart failure and chronic pain",
                "depression and chronic pain management"
            ]
        },
        difficulty="medium",
        expected_output_length="medium"
    ),
    PromptTemplate(
        name="patient_education",
        template="Create patient education materials explaining {topic} for a patient who {patient_characteristic}. Use clear, accessible language.",
        variables={
            "topic": [
                "how to use an insulin pen",
                "warning signs of stroke",
                "managing chronic pain without opioids",
                "preparing for colonoscopy",
                "lifestyle modifications for heart health",
                "understanding their cancer treatment options"
            ],
            "patient_characteristic": [
                "has limited health literacy",
                "is elderly and lives alone",
                "has young children and limited time",
                "is anxious about their diagnosis",
                "has cultural beliefs that affect treatment acceptance"
            ]
        },
        difficulty="medium",
        expected_output_length="medium"
    ),
]

MEDICAL_DOMAIN = DomainConfig(
    name="medical",
    description="Clinical reasoning, diagnosis, treatment planning, and patient education",
    templates=MEDICAL_TEMPLATES,
    system_prompts={
        "physician": "You are an experienced physician providing clinical reasoning. Be thorough but note this is for educational purposes, not actual medical advice.",
        "educator": "You are a medical educator helping students understand clinical decision-making. Explain your reasoning process clearly.",
        "consultant": "You are a specialist consultant providing detailed analysis of complex cases. Consider evidence-based guidelines and patient-specific factors."
    },
    evaluation_criteria=[
        "clinical_accuracy", "reasoning_quality", "safety_awareness",
        "evidence_basis", "patient_centeredness", "practical_applicability"
    ]
)


# =============================================================================
# GENERAL DOMAIN
# =============================================================================

GENERAL_TEMPLATES = [
    PromptTemplate(
        name="explain_concept",
        template="Explain {concept} to someone with {audience_level} background. Use analogies and examples to make it clear.",
        variables={
            "concept": [
                "how machine learning works",
                "the theory of relativity",
                "how the stock market functions",
                "the scientific method",
                "how vaccines work",
                "the basics of climate change",
                "how encryption protects data",
                "the principles of evolution"
            ],
            "audience_level": [
                "no technical", "a high school",
                "a college", "an expert"
            ]
        },
        difficulty="easy",
        expected_output_length="medium"
    ),
    PromptTemplate(
        name="compare_contrast",
        template="Compare and contrast {item1} and {item2}. Discuss their similarities, differences, and when you might choose one over the other.",
        variables={
            "item1": [
                "renewable and non-renewable energy",
                "capitalism and socialism",
                "iOS and Android",
                "traditional and digital marketing",
                "public and private education"
            ],
            "item2": [
                "their economic implications",
                "their environmental impact",
                "their social effects",
                "their practical applications",
                "their long-term sustainability"
            ]
        },
        difficulty="medium",
        expected_output_length="long"
    ),
    PromptTemplate(
        name="problem_solve",
        template="Help me solve this problem: {problem}. Walk through your reasoning step by step.",
        variables={
            "problem": [
                "I need to organize a team event for 50 people with a budget of $2000",
                "I'm trying to decide between two job offers with different trade-offs",
                "I want to learn a new skill but have limited time each week",
                "I need to have a difficult conversation with a colleague about their performance",
                "I'm trying to reduce my environmental footprint without major lifestyle changes"
            ]
        },
        difficulty="medium",
        expected_output_length="medium"
    ),
    PromptTemplate(
        name="summarize",
        template="Summarize the key points of {topic}. Provide a balanced overview covering main arguments and counterarguments.",
        variables={
            "topic": [
                "the debate over universal basic income",
                "the pros and cons of remote work",
                "arguments for and against nuclear energy",
                "the impact of social media on mental health",
                "the future of artificial intelligence",
                "the cryptocurrency and blockchain debate"
            ]
        },
        difficulty="medium",
        expected_output_length="long"
    ),
    PromptTemplate(
        name="analyze_situation",
        template="Analyze this situation: {situation}. What are the key factors to consider and what would you recommend?",
        variables={
            "situation": [
                "A company is deciding whether to expand internationally or focus on domestic growth",
                "A city is considering banning cars from the downtown area",
                "A university is debating whether to make standardized tests optional for admissions",
                "A family is deciding whether to rent or buy a home in the current market",
                "A nonprofit is choosing between two different approaches to achieve their mission"
            ]
        },
        difficulty="hard",
        expected_output_length="long"
    ),
]

GENERAL_DOMAIN = DomainConfig(
    name="general",
    description="General knowledge, reasoning, and problem-solving tasks",
    templates=GENERAL_TEMPLATES,
    system_prompts={
        "assistant": "You are a knowledgeable assistant helping to explain concepts and solve problems. Be clear, balanced, and thorough.",
        "teacher": "You are a patient teacher helping someone learn. Break down complex ideas and check for understanding.",
        "advisor": "You are a thoughtful advisor helping with decisions. Present multiple perspectives and help weigh trade-offs."
    },
    evaluation_criteria=[
        "accuracy", "clarity", "completeness",
        "balanced_perspective", "practical_usefulness", "reasoning_quality"
    ]
)


# =============================================================================
# COMPLEX REASONING DOMAIN (Pro-Advantage Tasks)
# =============================================================================

COMPLEX_REASONING_TEMPLATES = [
    # Multi-step Mathematical Reasoning
    PromptTemplate(
        name="mathematical_proof",
        template="Prove that {theorem}. Show your complete reasoning with each step clearly justified.",
        variables={
            "theorem": [
                "the sum of the first n odd numbers equals n²",
                "for any integer n, n³ - n is divisible by 6",
                "the square root of 2 is irrational",
                "there are infinitely many prime numbers",
                "the sum of angles in any triangle is 180 degrees (using parallel line properties)",
                "a number is divisible by 3 if and only if the sum of its digits is divisible by 3",
            ]
        },
        difficulty="hard",
        expected_output_length="long"
    ),
    PromptTemplate(
        name="multi_step_word_problem",
        template="{scenario} Show all calculations and explain your reasoning at each step.",
        variables={
            "scenario": [
                "A company's revenue grows 15% annually while costs grow 8%. Starting with revenue of $1M and costs of $800K, in which year does profit margin first exceed 40%? What is the total cumulative profit by that year?",
                "A water tank is being filled by pipe A at 3 liters/min and drained by pipe B at 2 liters/min. If the tank is 40% full (holds 500L total) and pipe A runs for 20 min before both run together, how long until the tank overflows?",
                "An investment grows at 7% annually for the first 5 years, then 5% for the next 5 years, then 3% thereafter. If I invest $10,000 today and add $1,000 each year, what is the value after 15 years?",
                "A train leaves Station A at 60 mph toward Station B. 30 minutes later, another train leaves B at 80 mph toward A. If the stations are 280 miles apart, at what time and location do they meet? How far is each from their origin?",
                "A bakery sells 200 loaves daily at $5 each. For every $0.50 price increase, sales drop by 10 loaves. What price maximizes revenue? What is the maximum revenue?",
            ]
        },
        difficulty="hard",
        expected_output_length="long"
    ),

    # Complex Algorithm Design
    PromptTemplate(
        name="algorithm_with_constraints",
        template="Design an algorithm for {problem}. Your solution must {constraints}. Analyze time and space complexity, prove correctness, and discuss edge cases.",
        variables={
            "problem": [
                "finding the longest palindromic substring in a string",
                "scheduling n jobs with deadlines and profits to maximize total profit",
                "detecting if a graph contains a negative cycle",
                "finding the median of a stream of numbers",
                "implementing an LFU (Least Frequently Used) cache with O(1) operations",
                "finding all strongly connected components in a directed graph",
            ],
            "constraints": [
                "achieve O(n) time complexity",
                "use O(1) extra space (in-place)",
                "handle concurrent access safely without using locks",
                "work correctly with integer overflow edge cases",
                "support undo/redo operations efficiently",
            ]
        },
        difficulty="hard",
        expected_output_length="long"
    ),
    PromptTemplate(
        name="system_tradeoffs",
        template="Design a {system_type}. You must optimize for these competing requirements: {requirements}. Explain your architectural decisions, the tradeoffs you made, and why.",
        variables={
            "system_type": [
                "distributed key-value store",
                "real-time multiplayer game server",
                "high-frequency trading matching engine",
                "globally distributed SQL database",
                "ML model serving infrastructure",
            ],
            "requirements": [
                "(1) sub-millisecond latency for reads, (2) strong consistency across regions, (3) 99.999% availability, (4) cost efficiency",
                "(1) handling 1 million concurrent users, (2) exactly-once event delivery, (3) real-time state synchronization, (4) graceful handling of network partitions",
                "(1) FIFO ordering guarantees, (2) nanosecond-level latency, (3) perfect audit trail, (4) zero message loss even during failures",
                "(1) ACID compliance, (2) horizontal scalability, (3) cross-region replication with <100ms lag, (4) support for complex joins",
                "(1) low latency (<50ms p99), (2) automatic scaling, (3) A/B testing support, (4) model version rollback within seconds",
            ]
        },
        difficulty="hard",
        expected_output_length="long"
    ),

    # Scientific Hypothesis Evaluation
    PromptTemplate(
        name="confounding_analysis",
        template="A study found that {finding}. Identify at least 5 potential confounding variables or alternative explanations. For each, explain the mechanism and propose a follow-up experiment to rule it out.",
        variables={
            "finding": [
                "people who drink coffee live longer than non-coffee drinkers",
                "students who take handwritten notes perform better than those typing notes",
                "countries with higher chocolate consumption have more Nobel laureates",
                "children who play video games have lower academic performance",
                "employees who work from home report higher job satisfaction",
                "regions with more ice cream sales have higher crime rates",
            ]
        },
        difficulty="hard",
        expected_output_length="long"
    ),
    PromptTemplate(
        name="experimental_critique",
        template="Critique this experimental design and results: {experiment}. Identify methodological flaws, statistical issues, and threats to validity. Propose improvements.",
        variables={
            "experiment": [
                "A drug trial with 50 patients showed 30% improvement vs placebo. P-value was 0.04. The trial was stopped early when interim analysis showed significance. They conclude the drug is effective.",
                "A survey of 1000 people found those who meditate are 40% less stressed. Participants self-selected into meditation and control groups. The meditation group also had higher average income.",
                "An A/B test for a website button color showed blue outperformed green (5.2% vs 4.8% conversion) with p=0.03. The test ran for 2 days during a holiday weekend. Sample was 10,000 per variant.",
                "A mouse study showed gene knockout increased lifespan by 25%. All knockout mice were male; controls were mixed. Mice were fed ad libitum. The study was not blinded.",
            ]
        },
        difficulty="hard",
        expected_output_length="long"
    ),

    # Nuanced Legal/Contract Analysis
    PromptTemplate(
        name="contract_hidden_risks",
        template="Analyze this contract clause for hidden risks and ambiguities that could be exploited:\n\n\"{clause}\"\n\nIdentify at least 5 specific risks, explain how each could be exploited, and propose protective language.",
        variables={
            "clause": [
                "Licensor grants Licensee a non-exclusive license to use the Software for internal business purposes. Licensor may update these terms at any time by posting to its website. Continued use constitutes acceptance.",
                "Contractor shall deliver the Project by the Completion Date. If delays occur due to circumstances beyond Contractor's reasonable control, the Completion Date shall be extended accordingly. Client shall pay within 30 days of invoice.",
                "Employee agrees that any invention conceived during employment belongs to Employer. Employee shall not engage in any business that competes with Employer during and for 2 years after employment.",
                "Vendor warrants that Products will be free from defects for 12 months. Vendor's sole liability is repair or replacement. IN NO EVENT SHALL VENDOR BE LIABLE FOR CONSEQUENTIAL DAMAGES.",
            ]
        },
        difficulty="hard",
        expected_output_length="long"
    ),

    # Multi-Constraint Optimization
    PromptTemplate(
        name="resource_allocation",
        template="{scenario} Find the optimal allocation and prove why it's optimal. Show the mathematical formulation.",
        variables={
            "scenario": [
                "You have 3 machines that can process 2 types of products. Machine A: 4 units of P1 or 2 units of P2 per hour. Machine B: 3 units of P1 or 4 units of P2 per hour. Machine C: 2 units of P1 or 5 units of P2 per hour. P1 sells for $10, P2 for $8. You need at least 100 P1 and 80 P2. Minimize total machine-hours while meeting demand.",
                "Allocate a $10M budget across 5 projects. Each project has diminishing returns: Project i gives utility = k_i * sqrt(investment_i). The k values are [5, 8, 3, 6, 4]. Additionally, Projects 1 and 2 combined must get at least $3M, and no single project can get more than 40% of the budget.",
                "Schedule 20 nurses across 7 days. Each day needs: 5 nurses for day shift, 4 for evening, 3 for night. Each nurse works exactly 5 days. No nurse can work more than 2 consecutive days. Minimize the maximum number of night shifts any nurse works.",
            ]
        },
        difficulty="hard",
        expected_output_length="long"
    ),
    PromptTemplate(
        name="decision_under_uncertainty",
        template="{scenario} Analyze the decision using expected value, utility theory, and risk considerations. Recommend the best course of action with full justification.",
        variables={
            "scenario": [
                "A startup can: (A) Accept a $5M acquisition offer now, (B) Raise Series A with 30% dilution and 60% chance of $50M exit in 3 years (40% chance of failure and $0), or (C) Bootstrap with 20% annual growth and sell in 5 years at 5x revenue (current revenue $500K). The founders have $200K in savings and no other income. Which option maximizes expected utility?",
                "A pharma company has a drug in Phase 2 trials. They can: (A) Sell rights now for $100M, (B) Continue to Phase 3 at $300M cost with 40% success probability leading to $2B in sales, or (C) Partner with Big Pharma for 50/50 split and shared Phase 3 costs. Recent competitor failures have raised regulatory scrutiny. What should they do?",
                "An investor has $1M. Options: (A) 100% in S&P 500 (expected 10% return, 15% std dev), (B) 60/40 stocks/bonds (7% return, 8% std dev), (C) A private deal with 50% chance of 3x return, 50% chance of losing 80%. The investor is 55, plans to retire at 60, and has $500K in other savings. What's the optimal allocation?",
            ]
        },
        difficulty="hard",
        expected_output_length="long"
    ),

    # Logical Paradox Resolution
    PromptTemplate(
        name="paradox_analysis",
        template="Analyze the {paradox}. Explain why it seems paradoxical, identify the hidden assumption or fallacy, and provide a clear resolution.",
        variables={
            "paradox": [
                "Unexpected Hanging Paradox: A judge tells a prisoner he will be hanged on a weekday next week, but it will be a surprise (he won't know the night before). The prisoner reasons he can't be hanged Friday (he'd know Thursday night), so not Thursday either, etc., concluding he can't be hanged. He's hanged Wednesday and is surprised.",
                "Newcomb's Problem: A predictor offers two boxes. Box A has $1000, Box B has either $0 or $1M. You can take both boxes or just B. The predictor predicted your choice: if you take both, B is empty; if you take only B, it contains $1M. The predictor is 99% accurate. What should you do?",
                "Ship of Theseus: A ship has all its planks gradually replaced over time. Is it the same ship? What if we rebuilt a second ship from the old planks?",
                "Voting Paradox: Three voters rank options A>B>C, B>C>A, and C>A>B. Majority prefers A to B, B to C, but C to A. How should we aggregate preferences?",
            ]
        },
        difficulty="hard",
        expected_output_length="long"
    ),
]

COMPLEX_REASONING_DOMAIN = DomainConfig(
    name="complex_reasoning",
    description="Multi-step reasoning, mathematical proofs, algorithm design, and nuanced analysis (Pro-advantage)",
    templates=COMPLEX_REASONING_TEMPLATES,
    system_prompts={
        "expert": "You are an expert problem solver with deep analytical skills. Show complete, rigorous reasoning. Every step must be justified. Identify edge cases and potential errors in your own logic.",
        "professor": "You are a professor grading a PhD qualifying exam. Provide solutions that would earn full marks: complete, rigorous, with all assumptions stated and corner cases handled.",
        "adversarial": "You are a critical analyst. Challenge assumptions, look for flaws, and stress-test all conclusions. If there's a way the answer could be wrong, find it."
    },
    evaluation_criteria=[
        "logical_validity",       # Are all reasoning steps valid?
        "completeness",           # Are all cases considered?
        "mathematical_rigor",     # Is the math correct and well-justified?
        "edge_case_handling",     # Are edge cases identified and handled?
        "assumption_clarity",     # Are assumptions explicitly stated?
        "solution_correctness",   # Is the final answer correct?
        "reasoning_depth",        # How deep is the analysis?
        "error_identification",   # Does it catch its own potential errors?
    ]
)


__all__ = [
    # Domain configurations
    "CODING_DOMAIN",
    "BIOLOGY_DOMAIN",
    "LEGAL_DOMAIN",
    "CREATIVE_DOMAIN",
    "FINANCE_DOMAIN",
    "MEDICAL_DOMAIN",
    "GENERAL_DOMAIN",
    "COMPLEX_REASONING_DOMAIN",
    # Template lists
    "CODING_TEMPLATES",
    "BIOLOGY_TEMPLATES",
    "LEGAL_TEMPLATES",
    "CREATIVE_TEMPLATES",
    "FINANCE_TEMPLATES",
    "MEDICAL_TEMPLATES",
    "GENERAL_TEMPLATES",
    "COMPLEX_REASONING_TEMPLATES",
]
