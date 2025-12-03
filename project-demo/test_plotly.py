
import plotly.express as px
import pandas as pd
import numpy as np

# Create dummy data
df = pd.DataFrame({
    "x": np.arange(10),
    "y": np.arange(10) + np.random.randn(10)
})

print("Attempting to create scatter plot with OLS trendline...")
try:
    fig = px.scatter(df, x="x", y="y", trendline="ols")
    print("SUCCESS: Scatter plot with trendline created.")
except Exception as e:
    print(f"FAILURE: {e}")
except ImportError as e:
    print(f"IMPORT ERROR: {e}")
