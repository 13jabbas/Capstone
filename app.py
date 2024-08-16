import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import f1_score, precision_score, recall_score, roc_auc_score, roc_curve
from sklearn.preprocessing import label_binarize, LabelEncoder
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from wordcloud import WordCloud

# Set page configuration
st.set_page_config(layout="wide")


# Load data
@st.cache_data
def load_data():
    df = pd.read_csv('LLMNER.csv')  # Modify path as needed
    hallucinations = pd.read_csv('Hallucination Confidence Score (3).csv')  # Modify path as needed
    return df, hallucinations

df, hallucinations = load_data()

# Streamlit Title and description
st.title("LLM Performance Dashboard")

# Layout for the entities section with metrics
st.header("Entity Metrics")

# Create a two-column layout
col1, col2 = st.columns([1, 4])  # col1 for the dropdown, col2 for gauges and ROC curve

# Micro F1 score, precision, recall, and ROC evaluation for each attribute
def evaluate_metrics(df, columns_to_evaluate):
    results = {}
    for col in columns_to_evaluate:
        y_true = df[f'{col} Checked'].dropna()
        y_pred = df[col].dropna()
        common_indices = y_true.index.intersection(y_pred.index)
        y_true = y_true.loc[common_indices]
        y_pred = y_pred.loc[common_indices]
        
        le = LabelEncoder()
        combined_labels = pd.concat([y_true, y_pred])
        le.fit(combined_labels)
        y_true_encoded = le.transform(y_true)
        y_pred_encoded = le.transform(y_pred)

        micro_f1 = f1_score(y_true_encoded, y_pred_encoded, average='micro')
        precision = precision_score(y_true_encoded, y_pred_encoded, average='micro')
        recall = recall_score(y_true_encoded, y_pred_encoded, average='micro')
        classes = le.classes_
        y_true_binarized = label_binarize(y_true_encoded, classes=range(len(classes)))
        y_pred_binarized = label_binarize(y_pred_encoded, classes=range(len(classes)))

        if y_true_binarized.shape[1] == 1:
            auc = roc_auc_score(y_true_encoded, y_pred_encoded)
            fpr, tpr, _ = roc_curve(y_true_encoded, y_pred_encoded)
        else:
            auc = roc_auc_score(y_true_binarized, y_pred_binarized, average='micro')
            fpr, tpr, _ = roc_curve(y_true_binarized.ravel(), y_pred_binarized.ravel())

        results[col] = {'Micro F1 Score': micro_f1, 'Precision': precision, 'Recall': recall, 'AUC': auc, 'FPR': fpr, 'TPR': tpr}
    
    return results

# Metrics evaluation
columns_to_evaluate = ['Action', 'Object', 'Feature', 'Ability', 'Agent', 'Environment']
results = evaluate_metrics(df, columns_to_evaluate)

# Sidebar for dropdown selection
with col1:
    st.subheader("Select Entity to View Metrics")
    selected_entity = st.selectbox("Choose an entity", columns_to_evaluate)

# Display the metrics for the selected entity as gauges
with col2:
    st.subheader(f"Metrics Gauges for {selected_entity}")
    metrics = results[selected_entity]

    # Create gauges for each metric using Plotly
    fig_gauges = make_subplots(rows=1, cols=4, subplot_titles=["Micro F1 Score", "Precision", "Recall", "AUC"], specs=[[{'type': 'indicator'}] * 4])

    fig_gauges.add_trace(go.Indicator(
        mode="gauge+number",
        value=metrics['Micro F1 Score'] * 100,
        title={'text': "Micro F1 Score"},
        gauge={'axis': {'range': [0, 100]}, 'bar': {'color': "darkblue"}}
    ), row=1, col=1)

    fig_gauges.add_trace(go.Indicator(
        mode="gauge+number",
        value=metrics['Precision'] * 100,
        title={'text': "Precision"},
        gauge={'axis': {'range': [0, 100]}, 'bar': {'color': "green"}}
    ), row=1, col=2)

    fig_gauges.add_trace(go.Indicator(
        mode="gauge+number",
        value=metrics['Recall'] * 100,
        title={'text': "Recall"},
        gauge={'axis': {'range': [0, 100]}, 'bar': {'color': "orange"}}
    ), row=1, col=3)

    fig_gauges.add_trace(go.Indicator(
        mode="gauge+number",
        value=metrics['AUC'] * 100,
        title={'text': "AUC"},
        gauge={'axis': {'range': [0, 100]}, 'bar': {'color': "red"}}
    ), row=1, col=4)

    fig_gauges.update_layout(height=400, width=1200, title_text=f"Accuracy Gauges for {selected_entity}")
    st.plotly_chart(fig_gauges)

    # Display ROC curve for selected entity
    st.subheader("ROC Curve")
    fig, ax = plt.subplots(figsize=(8, 6))
    ax.plot(metrics['FPR'], metrics['TPR'], label=f"{selected_entity} (AUC = {metrics['AUC']:.2f})")
    ax.plot([0, 1], [0, 1], 'k--', label="Random Guessing (AUC = 0.50)")
    ax.set_xlabel('False Positive Rate')
    ax.set_ylabel('True Positive Rate')
    ax.set_title(f'ROC Curve for {selected_entity}')
    ax.legend(loc='lower right')
    st.pyplot(fig)

# Add another section for hallucinations
st.header("Hallucinations Analysis")

# Word Cloud for Hallucinations
st.subheader("Word Cloud for Hallucinations")
new_df = hallucinations[hallucinations['Keyword Match Count'] == 0]
text = ' '.join(new_df['Description'].astype(str))
wordcloud = WordCloud(width=800, height=400, background_color='white').generate(text)
fig_wordcloud, ax = plt.subplots(figsize=(10, 5))
ax.imshow(wordcloud, interpolation='bilinear')
ax.axis('off')
st.pyplot(fig_wordcloud)



##HEATMEAP 


import altair as alt
import pandas as pd
import streamlit as st
import os
def make_heatmap(input_df, input_y, input_x, input_color, input_color_theme):
    # Ensure the columns used in the heatmap exist
    if not all(col in input_df.columns for col in [input_y, input_x, input_color]):
        st.error("One or more columns are missing in the DataFrame")
        return None

    # Ensure the color column is numeric
    if not pd.api.types.is_numeric_dtype(input_df[input_color]):
        st.error(f"The column '{input_color}' must be numeric.")
        return None

    # Create the heatmap
    heatmap = alt.Chart(input_df).mark_rect().encode(
        y=alt.Y(f'{input_y}:O', axis=alt.Axis(title="Review", titleFontSize=18, titlePadding=15, titleFontWeight=900, labelAngle=0)),
        x=alt.X(f'{input_x}:O', axis=alt.Axis(title="Description", titleFontSize=18, titlePadding=15, titleFontWeight=900)),
        color=alt.Color(f'{input_color}:Q',
                        legend=None,
                        scale=alt.Scale(scheme=input_color_theme)),
        stroke=alt.value('black'),
        strokeWidth=alt.value(0.25),
        tooltip=[
            alt.Tooltip(f'{input_y}:N', title='Review'),
            alt.Tooltip(f'{input_x}:N', title='Description'),
            alt.Tooltip(f'{input_color}:Q', title='Hallucination Score')
        ]
    ).properties(
        width=900,
        height=500  # Adjust height if needed
    ).configure_axis(
        labelFontSize=12,
        titleFontSize=12
    )
    return heatmap

# Load DataFrame (example code)

if os.path.exists(data_path):
    hallucinations_df = pd.read_csv('Hallucination Confidence Score (3).csv')
else:
    st.write("File not found.")
    hallucinations_df = pd.DataFrame()  # Empty DataFrame

# Generate heatmap if the DataFrame is not empty
if not hallucinations_df.empty:
    heatmap_chart = make_heatmap(
        hallucinations_df,
        input_y='Review Text Original', 
        input_x='Description Original',  
        input_color='Hallucination Confidence Score',
        input_color_theme='viridis'  
    )
    
    if heatmap_chart:
        st.altair_chart(heatmap_chart, use_container_width=True)
else:
    st.write("Data is not available or the DataFrame is empty.")
