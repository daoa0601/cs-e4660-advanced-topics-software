"""
Visualization constants for consistent styling across all charts.

Centralizes color definitions and chart configurations to eliminate
duplication across notebooks and analysis scripts.
"""

# Model colors - used throughout all visualizations
FLASH_COLOR = '#4ecdc4'  # Teal for Gemini Flash
PRO_COLOR = '#ff6b6b'    # Coral/Red for Gemini Pro

# Color mapping for model-based charts
MODEL_COLORS = {
    'gemini-2.5-flash': FLASH_COLOR,
    'gemini-2.5-pro': PRO_COLOR,
    'flash': FLASH_COLOR,
    'pro': PRO_COLOR,
}

# Plotly template for consistent styling
DEFAULT_TEMPLATE = 'plotly_white'

# Standard chart dimensions
CHART_CONFIG = {
    'width': 1000,
    'height': 600,
}

# Stage type colors for detailed breakdowns
STAGE_COLORS = {
    'generation': '#4ecdc4',
    'conversation': '#45b7d1',
    'thinking': '#96ceb4',
    'critique': '#ffeaa7',
    'refinement': '#dfe6e9',
    'extraction': '#74b9ff',
    'summarization': '#a29bfe',
    'validation': '#fd79a8',
    'action': '#00b894',
    'observation': '#6c5ce7',
}

# Pipeline complexity colors
COMPLEXITY_COLORS = {
    'simple': '#4ecdc4',
    'moderate': '#ffeaa7',
    'complex': '#ff6b6b',
}
