import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as bg

# Page Configuration
st.set_page_config(
    page_title="Darkstore Operational Analytic",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling
st.markdown("""
<style>
    .metric-card {
        background-color: #1E222D;
        border-radius: 10px;
        padding: 15px;
        border: 1px solid #2E3440;
    }
</style>
""", unsafe_allow_html=True)

# Load Data
@st.cache_data
def load_data():
    try:
        df = pd.read_csv("bb (1).csv")
        # Clean column headers
        df.columns = [c.replace('Ã\x83Â¯Ã\x82Â»Ã\x82Â¿', '').replace('ï»¿', '').strip() for c in df.columns]
        
        # Convert date/time columns
        if 'Order Time' in df.columns:
            df['Order_Time_dt'] = pd.to_datetime(df['Order Time'], errors='coerce')
        if 'Reachedgate Time' in df.columns:
            df['Reachedgate_Time_dt'] = pd.to_datetime(df['Reachedgate Time'], errors='coerce')
            
        # Convert numerical fields
        num_cols = [
            'Breached Duration (In Min)', 
            'Road Time (In Min)', 
            'Delivery Distance Travelled (km)',
            'Pickup Completed to Reached Gate (In Min)'
        ]
        for col in num_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
                
        # Fill missing rider names
        if '(Rider Name)' in df.columns:
            df['Rider Name'] = df['(Rider Name)'].fillna('Unassigned')
            
        return df
    except Exception as e:
        st.error(f"Error loading dataset: {e}")
        return pd.DataFrame()

df = load_data()

if df.empty:
    st.warning("Please ensure 'bb (1).csv' is uploaded to the root directory of your repository.")
    st.stop()

# Sidebar Filters
st.sidebar.title("⚡ Navigation & Filters")
st.sidebar.markdown("---")

# Darkstore / Location Filter
if 'Store Name' in df.columns:
    stores = ['All Stores'] + list(df['Store Name'].dropna().unique())
    selected_store = st.sidebar.selectbox("Select Darkstore Location", stores)
    if selected_store != 'All Stores':
        df = df[df['Store Name'] == selected_store]

# Rider Type Filter
if 'Rider Type' in df.columns:
    rider_types = ['All Fleet Types'] + list(df['Rider Type'].dropna().unique())
    selected_type = st.sidebar.selectbox("Select Fleet Type", rider_types)
    if selected_type != 'All Fleet Types':
        df = df[df['Rider Type'] == selected_type]

# Dashboard Header
st.title("⚡ Quick Commerce Darkstore Analytics")
st.markdown("Real-time operational dashboard monitoring fulfillment speeds, rider performance, and SLA breach metrics.")
st.markdown("---")

# Key Performance Indicators (KPIs)
col1, col2, col3, col4 = st.columns(4)

total_orders = len(df)
breached_orders = len(df[df['Breached'] == 'Yes']) if 'Breached' in df.columns else 0
breach_rate = (breached_orders / total_orders * 100) if total_orders > 0 else 0
avg_distance = df['Delivery Distance Travelled (km)'].mean() if 'Delivery Distance Travelled (km)' in df.columns else 0
avg_prep_time = df['Pickup Completed to Reached Gate (In Min)'].mean() if 'Pickup Completed to Reached Gate (In Min)' in df.columns else 0

with col1:
    st.metric("Total Orders", f"{total_orders:,}")
with col2:
    st.metric("SLA Breach Rate", f"{breach_rate:.1f}%", delta=f"{breached_orders} breaches", delta_color="inverse")
with col3:
    st.metric("Avg. Distance", f"{avg_distance:.2f} km")
with col4:
    st.metric("Avg. Prep Time", f"{avg_prep_time:.1f} min")

st.markdown("---")

# Visualizations Row 1
r1_col1, r1_col2 = st.columns(2)

with r1_col1:
    st.subheader("SLA Performance by Fleet Type")
    if 'Rider Type' in df.columns and 'Breached' in df.columns:
        fig_sla = px.histogram(
            df, x='Rider Type', color='Breached',
            barmode='stack',
            color_discrete_map={'No': '#00D26A', 'Yes': '#FF4D4D'},
            template='plotly_dark'
        )
        fig_sla.update_layout(margin=dict(l=20, r=20, t=30, b=20))
        st.plotly_chart(fig_sla, use_container_width=True)

with r1_col2:
    st.subheader("Hourly Order Velocity")
    if 'Order_Time_dt' in df.columns:
        df_time = df.dropna(subset=['Order_Time_dt']).copy()
        df_time['Hour'] = df_time['Order_Time_dt'].dt.hour
        hourly_counts = df_time.groupby('Hour').size().reset_index(name='Orders')
        
        fig_hourly = px.line(
            hourly_counts, x='Hour', y='Orders',
            markers=True,
            line_shape='spline',
            color_discrete_sequence=['#00D26A'],
            template='plotly_dark'
        )
        fig_hourly.update_layout(margin=dict(l=20, r=20, t=30, b=20))
        st.plotly_chart(fig_hourly, use_container_width=True)

# Visualizations Row 2
r2_col1, r2_col2 = st.columns(2)

with r2_col1:
    st.subheader("Distance vs. Road Time (Breach Analysis)")
    if 'Delivery Distance Travelled (km)' in df.columns and 'Road Time (In Min)' in df.columns:
        fig_scatter = px.scatter(
            df, 
            x='Delivery Distance Travelled (km)', 
            y='Road Time (In Min)',
            color='Breached' if 'Breached' in df.columns else None,
            color_discrete_map={'No': '#00D26A', 'Yes': '#FF4D4D'},
            hover_data=['Rider Name'] if 'Rider Name' in df.columns else None,
            opacity=0.7,
            template='plotly_dark'
        )
        fig_scatter.update_layout(margin=dict(l=20, r=20, t=30, b=20))
        st.plotly_chart(fig_scatter, use_container_width=True)

with r2_col2:
    st.subheader("Top Active Fleet Riders")
    if 'Rider Name' in df.columns:
        top_riders = df['Rider Name'].value_counts().head(10).reset_index()
        top_riders.columns = ['Rider Name', 'Completed Orders']
        
        fig_riders = px.bar(
            top_riders,
            x='Completed Orders',
            y='Rider Name',
            orientation='h',
            color='Completed Orders',
            color_continuous_scale='Greens',
            template='plotly_dark'
        )
        fig_riders.update_layout(yaxis=dict(autorange="reversed"), margin=dict(l=20, r=20, t=30, b=20))
        st.plotly_chart(fig_riders, use_container_width=True)

# Data Table Preview
st.markdown("---")
st.subheader("Filtered Operational Logs")
st.dataframe(df, use_container_width=True)
