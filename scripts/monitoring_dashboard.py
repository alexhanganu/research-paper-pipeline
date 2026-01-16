"""
Simple monitoring dashboard to view processing metrics and CloudWatch data.
Run with: streamlit run monitoring_dashboard.py
"""

try:
    import streamlit as st
    import pandas as pd
    import plotly.express as px
    import plotly.graph_objects as go
    from datetime import datetime, timedelta
    import json
    from pathlib import Path
    import boto3
    
    STREAMLIT_AVAILABLE = True
except ImportError:
    STREAMLIT_AVAILABLE = False
    print("Streamlit not installed. Install with: pip install streamlit plotly")

if not STREAMLIT_AVAILABLE:
    exit(1)

st.set_page_config(
    page_title="Research Paper Processing Dashboard",
    page_icon="📄",
    layout="wide"
)

st.title("📄 Research Paper Processing Dashboard")
st.markdown("---")

# Sidebar for configuration
st.sidebar.header("Configuration")
output_dir = st.sidebar.text_input("Output Directory", "project/outputs")
use_cloudwatch = st.sidebar.checkbox("Fetch CloudWatch Metrics", value=False)
provider = st.sidebar.selectbox("Provider Filter", ["All", "anthropic", "openai"])

# Helper functions
def load_local_metrics(output_dir):
    """Load metrics from local JSON files"""
    metrics_files = list(Path(output_dir).glob("metrics_*.json"))
    if not metrics_files:
        return None
    
    all_metrics = []
    for file in sorted(metrics_files, reverse=True)[:10]:  # Last 10 runs
        with open(file, 'r') as f:
            metrics = json.load(f)
            metrics['file'] = file.name
            all_metrics.append(metrics)
    
    return pd.DataFrame(all_metrics)

def load_results(output_dir, provider_filter="All"):
    """Load processing results from CSV files"""
    csv_files = list(Path(output_dir).glob("paper_summaries_*.csv"))
    
    if not csv_files:
        return None
    
    all_results = []
    for csv_file in csv_files:
        try:
            df = pd.read_csv(csv_file)
            if provider_filter != "All":
                df = df[df['api_provider'] == provider_filter]
            all_results.append(df)
        except Exception as e:
            st.sidebar.error(f"Error loading {csv_file.name}: {e}")
    
    if all_results:
        return pd.concat(all_results, ignore_index=True)
    return None

def get_cloudwatch_metrics(namespace='ResearchPaperProcessing', hours=24):
    """Fetch metrics from CloudWatch"""
    try:
        cloudwatch = boto3.client('cloudwatch')
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=hours)
        
        metrics_to_fetch = [
            'ProcessingSuccess',
            'ProcessingFailure',
            'AverageQualityScore',
            'TotalBiomarkers'
        ]
        
        all_data = {}
        for metric_name in metrics_to_fetch:
            response = cloudwatch.get_metric_statistics(
                Namespace=namespace,
                MetricName=metric_name,
                StartTime=start_time,
                EndTime=end_time,
                Period=3600,  # 1 hour
                Statistics=['Sum', 'Average'],
                Dimensions=[{'Name': 'Provider', 'Value': provider.lower()}] if provider != "All" else []
            )
            
            all_data[metric_name] = pd.DataFrame(response['Datapoints'])
        
        return all_data
    except Exception as e:
        st.error(f"Error fetching CloudWatch metrics: {e}")
        return None

# Load data
metrics_df = load_local_metrics(output_dir)
results_df = load_results(output_dir, provider)

# Main dashboard
if metrics_df is not None and not metrics_df.empty:
    # Key metrics
    col1, col2, col3, col4, col5 = st.columns(5)
    
    latest = metrics_df.iloc[0]
    
    with col1:
        st.metric(
            "Total Papers",
            f"{latest['total_papers']:,}",
            delta=None
        )
    
    with col2:
        success_rate = (latest['successful'] / latest['total_papers'] * 100) if latest['total_papers'] > 0 else 0
        st.metric(
            "Success Rate",
            f"{success_rate:.1f}%",
            delta=None
        )
    
    with col3:
        st.metric(
            "Avg Quality Score",
            f"{latest['average_quality_score']:.2f}",
            delta=None
        )
    
    with col4:
        st.metric(
            "Papers/Min",
            f"{latest['papers_per_minute']:.1f}",
            delta=None
        )
    
    with col5:
        st.metric(
            "Biomarkers Found",
            f"{latest['total_biomarkers_extracted']:,}",
            delta=None
        )
    
    st.markdown("---")
    
    # Processing trends
    st.subheader("📈 Processing Trends")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Success/Failure over time
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=metrics_df['timestamp'],
            y=metrics_df['successful'],
            name='Successful',
            marker_color='green'
        ))
        fig.add_trace(go.Bar(
            x=metrics_df['timestamp'],
            y=metrics_df['failed'],
            name='Failed',
            marker_color='red'
        ))
        fig.update_layout(
            title='Success vs Failure Rate',
            xaxis_title='Run',
            yaxis_title='Count',
            barmode='stack',
            height=400
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Quality score trend
        fig = px.line(
            metrics_df,
            x='timestamp',
            y='average_quality_score',
            title='Average Quality Score Over Time',
            markers=True
        )
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
    
    # Processing speed
    fig = px.bar(
        metrics_df,
        x='timestamp',
        y='papers_per_minute',
        title='Processing Speed (Papers per Minute)',
        color='provider'
    )
    fig.update_layout(height=400)
    st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("---")

# Results analysis
if results_df is not None and not results_df.empty:
    st.subheader("📊 Results Analysis")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Status distribution
        status_counts = results_df['status'].value_counts()
        fig = px.pie(
            values=status_counts.values,
            names=status_counts.index,
            title='Processing Status Distribution'
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Provider comparison
        if 'api_provider' in results_df.columns:
            provider_stats = results_df.groupby('api_provider').agg({
                'status': lambda x: (x == 'success').sum(),
                'quality_score': 'mean'
            }).reset_index()
            provider_stats.columns = ['Provider', 'Successful', 'Avg Quality']
            
            fig = go.Figure()
            fig.add_trace(go.Bar(
                x=provider_stats['Provider'],
                y=provider_stats['Successful'],
                name='Successful Papers',
                yaxis='y'
            ))
            fig.add_trace(go.Scatter(
                x=provider_stats['Provider'],
                y=provider_stats['Avg Quality'],
                name='Avg Quality',
                yaxis='y2',
                mode='markers+lines',
                marker=dict(size=10)
            ))
            fig.update_layout(
                title='Provider Comparison',
                yaxis=dict(title='Successful Papers'),
                yaxis2=dict(title='Avg Quality Score', overlaying='y', side='right'),
                height=400
            )
            st.plotly_chart(fig, use_container_width=True)
    
    # Publication year distribution
    if 'year' in results_df.columns:
        year_data = results_df[results_df['year'].notna() & (results_df['year'] != 'Not found')]
        if not year_data.empty:
            year_counts = year_data['year'].value_counts().sort_index()
            fig = px.bar(
                x=year_counts.index,
                y=year_counts.values,
                title='Papers by Publication Year',
                labels={'x': 'Year', 'y': 'Count'}
            )
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
    
    # Biomarker analysis
    if 'num_biomarkers' in results_df.columns:
        st.subheader("🧬 Biomarker Extraction Analysis")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            total_biomarkers = results_df['num_biomarkers'].sum()
            st.metric("Total Biomarkers Extracted", f"{total_biomarkers:,}")
        
        with col2:
            avg_biomarkers = results_df[results_df['num_biomarkers'] > 0]['num_biomarkers'].mean()
            st.metric("Avg Biomarkers per Paper", f"{avg_biomarkers:.1f}")
        
        with col3:
            papers_with_biomarkers = (results_df['num_biomarkers'] > 0).sum()
            pct_with_biomarkers = papers_with_biomarkers / len(results_df) * 100
            st.metric("Papers with Biomarkers", f"{pct_with_biomarkers:.1f}%")
        
        # Biomarker distribution
        fig = px.histogram(
            results_df[results_df['num_biomarkers'] > 0],
            x='num_biomarkers',
            title='Distribution of Biomarkers per Paper',
            nbins=20
        )
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("---")
    
    # Recent papers table
    st.subheader("📑 Recent Papers Processed")
    display_cols = ['filename', 'status', 'api_provider', 'title', 'authors', 'year', 'quality_score', 'num_biomarkers']
    display_cols = [col for col in display_cols if col in results_df.columns]
    st.dataframe(
        results_df[display_cols].head(20),
        use_container_width=True,
        height=400
    )

# CloudWatch metrics
if use_cloudwatch:
    st.markdown("---")
    st.subheader("☁️ CloudWatch Metrics (Last 24 Hours)")
    
    cw_data = get_cloudwatch_metrics()
    if cw_data:
        for metric_name, df in cw_data.items():
            if not df.empty:
                df['Timestamp'] = pd.to_datetime(df['Timestamp'])
                df = df.sort_values('Timestamp')
                
                stat = 'Sum' if metric_name in ['ProcessingSuccess', 'ProcessingFailure', 'TotalBiomarkers'] else 'Average'
                
                fig = px.line(
                    df,
                    x='Timestamp',
                    y=stat,
                    title=f'{metric_name} - {stat}',
                    markers=True
                )
                st.plotly_chart(fig, use_container_width=True)

# No data message
if metrics_df is None and results_df is None:
    st.warning("No data found. Please run the pipeline first to generate metrics and results.")
    st.info(f"Looking for data in: {output_dir}")

# Refresh button
if st.sidebar.button("🔄 Refresh Data"):
    st.rerun()