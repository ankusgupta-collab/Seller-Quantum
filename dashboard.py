"""
Seller Promo Incrementality Dashboard
Interactive Streamlit dashboard for analyzing seller promo performance
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from datetime import datetime, timedelta

# Page config
st.set_page_config(
    page_title="Seller Promo Incrementality Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1f77b4;
        margin-bottom: 0.5rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
    .positive {
        color: #2ecc71;
        font-weight: 700;
    }
    .negative {
        color: #e74c3c;
        font-weight: 700;
    }
</style>
""", unsafe_allow_html=True)

# Database connection function
@st.cache_resource
def get_db_connection():
    """
    Setup database connection
    Replace with your actual connection details
    """
    import pymysql
    # Example - update with your credentials
    # conn = pymysql.connect(
    #     host='your_host',
    #     user='your_user',
    #     password='your_password',
    #     database='your_database'
    # )
    # return conn
    return None  # Placeholder

# SQL Query
MAIN_QUERY = """
-- Paste the content from seller_promo_incrementality_CUSTOMIZED.sql here
-- Or load from file
"""

@st.cache_data(ttl=3600)
def load_data(query=None, use_sample=True):
    """
    Load data from database or generate sample data
    """
    if use_sample:
        # Generate sample data for demo
        np.random.seed(42)
        n_sellers = 150
        promos = ['Q1_Flash_Sale', 'Spring_Boost', 'Easter_Promo', 'Category_Push']

        data = []
        for promo in promos:
            n_promo_sellers = np.random.randint(30, 50)
            for i in range(n_promo_sellers):
                pre_gmv = np.random.exponential(5000) + 100
                lift_pct = np.random.normal(15, 25)  # Average 15% lift
                during_gmv = pre_gmv * (1 + lift_pct/100)
                post_gmv = during_gmv * np.random.uniform(0.8, 0.95)

                data.append({
                    'promo_name': promo,
                    'slr_id': f'SLR_{i:04d}',
                    'slr_cntry_cd': np.random.choice(['US', 'UK', 'DE', 'AU', 'CA'], p=[0.5, 0.2, 0.15, 0.1, 0.05]),
                    'short_site_name': np.random.choice(['US', 'UK', 'DE', 'AU', 'CA'], p=[0.5, 0.2, 0.15, 0.1, 0.05]),
                    'bsns_vrtcl_name': np.random.choice(['Fashion', 'Electronics', 'Home & Garden', 'Parts & Accessories', 'Collectibles']),
                    'b2c_c2c_flag': np.random.choice(['B2C', 'C2C'], p=[0.6, 0.4]),
                    'pre_gmv_usd': pre_gmv,
                    'during_gmv_usd': during_gmv,
                    'post_gmv_usd': post_gmv,
                    'pre_revenue_usd': pre_gmv * 1.15,
                    'during_revenue_usd': during_gmv * 1.15,
                    'post_revenue_usd': post_gmv * 1.15,
                    'pre_listings': int(np.random.poisson(20) + 5),
                    'during_listings': int(np.random.poisson(25) + 5),
                    'post_listings': int(np.random.poisson(22) + 5),
                    'pre_transactions': int(np.random.poisson(15) + 2),
                    'during_transactions': int(np.random.poisson(20) + 2),
                    'post_transactions': int(np.random.poisson(17) + 2),
                    'delta_gmv_usd': during_gmv - pre_gmv,
                    'incremental_gmv_usd': during_gmv - pre_gmv,
                    'incremental_revenue_usd': (during_gmv - pre_gmv) * 1.15,
                    'incremental_listings': int(np.random.normal(5, 3)),
                    'incremental_transactions': int(np.random.normal(5, 3)),
                    'gmv_lift_pct': lift_pct,
                    'revenue_lift_pct': lift_pct * 1.05,
                    'transaction_lift_pct': lift_pct * 0.9,
                    'listing_lift_pct': lift_pct * 1.1,
                    'seller_size_cohort': np.random.choice([
                        'Small Seller (<$1K)',
                        'Medium Seller ($1K-$10K)',
                        'Large Seller ($10K-$100K)'
                    ], p=[0.4, 0.4, 0.2]),
                    'performance_tier': 'Good Performer' if lift_pct > 10 else 'Modest Lift',
                    'pre_period_start': '2026-01-01',
                    'promo_period_start': '2026-02-01',
                    'promo_period_end': '2026-02-28',
                })

        df = pd.DataFrame(data)
        return df
    else:
        # Load from database
        conn = get_db_connection()
        if conn:
            df = pd.read_sql(query or MAIN_QUERY, conn)
            return df
        else:
            st.error("Database connection not configured. Using sample data.")
            return load_data(use_sample=True)

# Main app
def main():
    # Header
    st.markdown('<p class="main-header">📊 Seller Promo Incrementality Dashboard</p>', unsafe_allow_html=True)
    st.markdown("**Deep dive analysis for individual seller promotions**")

    # Sidebar
    st.sidebar.header("🎯 Select Promo")

    # Data source toggle
    use_sample = st.sidebar.checkbox("Use Sample Data", value=True,
                                     help="Uncheck to connect to live database")

    # Load data
    with st.spinner("Loading data..."):
        df = load_data(use_sample=use_sample)

    if df is None or len(df) == 0:
        st.error("No data available")
        return

    # MAIN FILTER: Promo Selection (REQUIRED - No "All" option)
    all_promos = sorted(df['promo_name'].unique().tolist())

    st.sidebar.markdown("### 📌 Primary Filter")
    selected_promo = st.sidebar.selectbox(
        "Select Promo to Analyze",
        all_promos,
        help="Choose one promo to deep dive into its performance"
    )

    # Filter data to selected promo first
    promo_df = df[df['promo_name'] == selected_promo].copy()

    # Show promo date range
    if len(promo_df) > 0:
        promo_start = promo_df['promo_period_start'].iloc[0]
        promo_end = promo_df['promo_period_end'].iloc[0]
        st.sidebar.info(f"📅 Promo Period:\n{promo_start} to {promo_end}")

    # Optional: Compare with another promo
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📊 Compare (Optional)")
    enable_comparison = st.sidebar.checkbox("Compare with another promo", value=False)

    compare_promo = None
    compare_df = None
    if enable_comparison:
        other_promos = [p for p in all_promos if p != selected_promo]
        if len(other_promos) > 0:
            compare_promo = st.sidebar.selectbox("Compare with", other_promos)
            compare_df = df[df['promo_name'] == compare_promo].copy()

    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🔍 Additional Filters")

    # Secondary filters (with "All" option for drilling down within the promo)
    all_sites = ['All'] + sorted(promo_df['short_site_name'].unique().tolist())
    selected_site = st.sidebar.selectbox("Site", all_sites)

    all_verticals = ['All'] + sorted(promo_df['bsns_vrtcl_name'].unique().tolist())
    selected_vertical = st.sidebar.selectbox("Business Vertical", all_verticals)

    all_cohorts = ['All'] + sorted(promo_df['seller_size_cohort'].unique().tolist())
    selected_cohort = st.sidebar.selectbox("Seller Size", all_cohorts)

    # Apply secondary filters
    filtered_df = promo_df.copy()
    if selected_site != 'All':
        filtered_df = filtered_df[filtered_df['short_site_name'] == selected_site]
    if selected_vertical != 'All':
        filtered_df = filtered_df[filtered_df['bsns_vrtcl_name'] == selected_vertical]
    if selected_cohort != 'All':
        filtered_df = filtered_df[filtered_df['seller_size_cohort'] == selected_cohort]

    # Tabs
    if enable_comparison and compare_promo:
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "📈 Executive Summary",
            "🔍 Deep Dive",
            "👥 Seller-Level",
            "💰 ROI Analysis",
            "⚖️ Promo Comparison"
        ])
    else:
        tab1, tab2, tab3, tab4 = st.tabs([
            "📈 Executive Summary",
            "🔍 Deep Dive",
            "👥 Seller-Level",
            "💰 ROI Analysis"
        ])
        tab5 = None

    # TAB 1: EXECUTIVE SUMMARY
    with tab1:
        # Promo Header
        st.markdown(f"## 🎯 {selected_promo}")
        if len(filtered_df) > 0:
            promo_start = filtered_df['promo_period_start'].iloc[0]
            promo_end = filtered_df['promo_period_end'].iloc[0]
            st.markdown(f"**Period:** {promo_start} to {promo_end}")

        # KPIs
        col1, col2, col3, col4, col5 = st.columns(5)

        total_incremental_gmv = filtered_df['incremental_gmv_usd'].sum()
        total_incremental_rev = filtered_df['incremental_revenue_usd'].sum()
        avg_lift = filtered_df['gmv_lift_pct'].mean()
        median_lift = filtered_df['gmv_lift_pct'].median()
        num_sellers = filtered_df['slr_id'].nunique()
        avg_gmv_per_seller = total_incremental_gmv / num_sellers if num_sellers > 0 else 0

        with col1:
            st.metric(
                "Total Incremental GMV",
                f"${total_incremental_gmv:,.0f}",
                delta=f"{avg_lift:.1f}% avg lift"
            )

        with col2:
            st.metric(
                "Incremental Revenue",
                f"${total_incremental_rev:,.0f}"
            )

        with col3:
            st.metric(
                "Average GMV Lift %",
                f"{avg_lift:.1f}%",
                delta=f"Median: {median_lift:.1f}%"
            )

        with col4:
            st.metric(
                "Sellers in Promo",
                f"{num_sellers:,}"
            )
            

        with col5:
            st.metric(
                "Avg Incremental GMV/Seller",
                f"${avg_gmv_per_seller:,.0f}"
            )

        st.markdown("---")

        # Charts row 1
        col1, col2 = st.columns(2)

        with col1:
            # Incremental GMV by Seller Size
            st.subheader("Incremental GMV by Seller Size")
            size_summary = filtered_df.groupby('seller_size_cohort').agg({
                'incremental_gmv_usd': 'sum',
                'gmv_lift_pct': 'mean',
                'slr_id': 'nunique'
            }).reset_index()
            size_summary.columns = ['Seller Size', 'Incremental GMV', 'Avg Lift %', 'Sellers']
            size_summary = size_summary.sort_values('Incremental GMV', ascending=True)

            fig = px.bar(
                size_summary,
                x='Incremental GMV',
                y='Seller Size',
                orientation='h',
                color='Avg Lift %',
                color_continuous_scale='RdYlGn',
                text='Incremental GMV',
                hover_data=['Sellers', 'Avg Lift %']
            )
            fig.update_traces(texttemplate='$%{text:,.0f}', textposition='outside')
            fig.update_layout(height=400, showlegend=False)
            st.plotly_chart(fig, width='stretch')

        with col2:
            # Performance distribution
            st.subheader("Seller Performance Distribution")
            perf_dist = filtered_df['performance_tier'].value_counts().reset_index()
            perf_dist.columns = ['Performance Tier', 'Count']

            fig = px.pie(
                perf_dist,
                values='Count',
                names='Performance Tier',
                color='Performance Tier',
                color_discrete_map={
                    'High Performer': '#2ecc71',
                    'Good Performer': '#3498db',
                    'Modest Lift': '#f39c12',
                    'No Change': '#95a5a6',
                    'Negative Impact': '#e74c3c'
                }
            )
            fig.update_layout(height=400)
            st.plotly_chart(fig, width='stretch')

        # Charts row 2
        st.subheader("Pre vs During vs Post Performance")

        # Aggregate by period
        period_data = pd.DataFrame({
            'Period': ['Pre', 'During', 'Post'],
            'GMV': [
                filtered_df['pre_gmv_usd'].sum(),
                filtered_df['during_gmv_usd'].sum(),
                filtered_df['post_gmv_usd'].sum()
            ],
            'Transactions': [
                filtered_df['pre_transactions'].sum(),
                filtered_df['during_transactions'].sum(),
                filtered_df['post_transactions'].sum()
            ]
        })

        fig = make_subplots(
            rows=1, cols=2,
            subplot_titles=('GMV by Period', 'Transactions by Period')
        )

        fig.add_trace(
            go.Bar(x=period_data['Period'], y=period_data['GMV'],
                   name='GMV', marker_color=['#95a5a6', '#3498db', '#e67e22']),
            row=1, col=1
        )

        fig.add_trace(
            go.Bar(x=period_data['Period'], y=period_data['Transactions'],
                   name='Transactions', marker_color=['#95a5a6', '#3498db', '#e67e22']),
            row=1, col=2
        )

        fig.update_layout(height=400, showlegend=False)
        st.plotly_chart(fig, width="stretch")

        # Top performers table
        st.subheader("Top 10 Performing Sellers")
        top_sellers = filtered_df.nlargest(10, 'incremental_gmv_usd')[
            ['slr_id', 'promo_name', 'seller_size_cohort', 'incremental_gmv_usd',
             'gmv_lift_pct', 'pre_gmv_usd', 'during_gmv_usd']
        ].copy()
        top_sellers.columns = ['Seller ID', 'Promo', 'Size', 'Incremental GMV',
                               'Lift %', 'Pre GMV', 'During GMV']

        # Format numbers
        top_sellers['Incremental GMV'] = top_sellers['Incremental GMV'].apply(lambda x: f'${x:,.0f}')
        top_sellers['Pre GMV'] = top_sellers['Pre GMV'].apply(lambda x: f'${x:,.0f}')
        top_sellers['During GMV'] = top_sellers['During GMV'].apply(lambda x: f'${x:,.0f}')
        top_sellers['Lift %'] = top_sellers['Lift %'].apply(lambda x: f'{x:.1f}%')

        st.dataframe(top_sellers, width='stretch', hide_index=True)

    # TAB 2: DEEP DIVE
    with tab2:
        st.header("Deep Dive Analysis")

        col1, col2 = st.columns(2)

        with col1:
            # By vertical
            st.subheader("Incrementality by Business Vertical")
            vertical_summary = filtered_df.groupby('bsns_vrtcl_name').agg({
                'incremental_gmv_usd': 'sum',
                'gmv_lift_pct': 'mean'
            }).reset_index()

            fig = px.treemap(
                vertical_summary,
                path=['bsns_vrtcl_name'],
                values='incremental_gmv_usd',
                color='gmv_lift_pct',
                color_continuous_scale='RdYlGn',
                labels={'gmv_lift_pct': 'Avg Lift %'}
            )
            fig.update_layout(height=400)
            st.plotly_chart(fig, width='stretch')

        with col2:
            # By geography
            st.subheader("Incrementality by Geography")
            geo_summary = filtered_df.groupby('slr_cntry_cd').agg({
                'incremental_gmv_usd': 'sum',
                'slr_id': 'nunique'
            }).reset_index()
            geo_summary.columns = ['Country', 'Incremental GMV', 'Sellers']
            geo_summary = geo_summary.sort_values('Incremental GMV', ascending=False)

            fig = px.bar(
                geo_summary,
                x='Country',
                y='Incremental GMV',
                color='Sellers',
                text='Incremental GMV',
                color_continuous_scale='Blues'
            )
            fig.update_traces(texttemplate='$%{text:,.0f}', textposition='outside')
            fig.update_layout(height=400)
            st.plotly_chart(fig, width='stretch')

        # Seller size cohort analysis
        st.subheader("Performance by Seller Size Cohort")
        cohort_summary = filtered_df.groupby('seller_size_cohort').agg({
            'incremental_gmv_usd': ['sum', 'mean'],
            'gmv_lift_pct': 'mean',
            'slr_id': 'nunique'
        }).reset_index()
        cohort_summary.columns = ['Cohort', 'Total Incremental GMV', 'Avg Incremental GMV',
                                   'Avg Lift %', 'Num Sellers']

        fig = go.Figure()
        fig.add_trace(go.Bar(
            name='Total Incremental GMV',
            x=cohort_summary['Cohort'],
            y=cohort_summary['Total Incremental GMV'],
            yaxis='y',
            marker_color='#3498db'
        ))
        fig.add_trace(go.Scatter(
            name='Avg Lift %',
            x=cohort_summary['Cohort'],
            y=cohort_summary['Avg Lift %'],
            yaxis='y2',
            mode='lines+markers',
            marker=dict(size=10, color='#e74c3c'),
            line=dict(width=3, color='#e74c3c')
        ))

        fig.update_layout(
            yaxis=dict(title='Total Incremental GMV ($)'),
            yaxis2=dict(title='Avg Lift %', overlaying='y', side='right'),
            height=400,
            hovermode='x unified'
        )
        st.plotly_chart(fig, width="stretch")

        # Data table
        st.dataframe(cohort_summary.style.format({
            'Total Incremental GMV': '${:,.0f}',
            'Avg Incremental GMV': '${:,.0f}',
            'Avg Lift %': '{:.1f}%',
            'Num Sellers': '{:,.0f}'
        }), width='stretch', hide_index=True)

    # TAB 3: SELLER-LEVEL
    with tab3:
        st.header("Seller-Level Detail")

        # Scatter plot
        st.subheader("Seller Performance Scatter")

        # Create size column with absolute values to avoid negative sizes
        plot_df = filtered_df.copy()
        plot_df['lift_size'] = np.abs(plot_df['gmv_lift_pct']) + 1  # Add 1 to ensure minimum size

        fig = px.scatter(
            plot_df,
            x='pre_gmv_usd',
            y='incremental_gmv_usd',
            color='performance_tier',
            size='lift_size',
            hover_data=['slr_id', 'promo_name', 'during_gmv_usd', 'gmv_lift_pct'],
            labels={
                'pre_gmv_usd': 'Baseline GMV (Pre-Period)',
                'incremental_gmv_usd': 'Incremental GMV',
                'gmv_lift_pct': 'Lift %'
            },
            color_discrete_map={
                'High Performer': '#2ecc71',
                'Good Performer': '#3498db',
                'Modest Lift': '#f39c12',
                'No Change': '#95a5a6',
                'Negative Impact': '#e74c3c'
            }
        )
        fig.add_hline(y=0, line_dash="dash", line_color="gray",
                     annotation_text="Break-even")
        fig.update_layout(height=500)
        st.plotly_chart(fig, width="stretch")

        # Distribution histogram
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Lift % Distribution")
            fig = px.histogram(
                filtered_df,
                x='gmv_lift_pct',
                nbins=30,
                labels={'gmv_lift_pct': 'GMV Lift %'},
                color_discrete_sequence=['#3498db']
            )
            fig.add_vline(x=0, line_dash="dash", line_color="red")
            fig.add_vline(x=filtered_df['gmv_lift_pct'].median(),
                         line_dash="dash", line_color="green",
                         annotation_text=f"Median: {filtered_df['gmv_lift_pct'].median():.1f}%")
            fig.update_layout(height=350)
            st.plotly_chart(fig, width='stretch')

        with col2:
            st.subheader("Incremental GMV Distribution")
            fig = px.histogram(
                filtered_df,
                x='incremental_gmv_usd',
                nbins=30,
                labels={'incremental_gmv_usd': 'Incremental GMV ($)'},
                color_discrete_sequence=['#e74c3c']
            )
            fig.add_vline(x=0, line_dash="dash", line_color="red")
            st.plotly_chart(fig, width='stretch')

        # Full seller table
        st.subheader("All Sellers - Detailed View")

        seller_table = filtered_df[[
            'slr_id', 'promo_name', 'seller_size_cohort', 'slr_cntry_cd',
            'pre_gmv_usd', 'during_gmv_usd', 'post_gmv_usd',
            'incremental_gmv_usd', 'gmv_lift_pct', 'performance_tier'
        ]].copy().sort_values('incremental_gmv_usd', ascending=False)

        seller_table.columns = [
            'Seller ID', 'Promo', 'Size', 'Country',
            'Pre GMV', 'During GMV', 'Post GMV',
            'Incremental GMV', 'Lift %', 'Performance'
        ]

        st.dataframe(
            seller_table.style.format({
                'Pre GMV': '${:,.0f}',
                'During GMV': '${:,.0f}',
                'Post GMV': '${:,.0f}',
                'Incremental GMV': '${:,.0f}',
                'Lift %': '{:.1f}%'
            }).background_gradient(
                subset=['Incremental GMV', 'Lift %'],
                cmap='RdYlGn',
                vmin=-20,
                vmax=50
            ),
            width='stretch',
            height=400,
            hide_index=True
        )

        # Download button
        csv = seller_table.to_csv(index=False)
        st.download_button(
            label="📥 Download Seller Data as CSV",
            data=csv,
            file_name=f"seller_promo_data_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )

    # TAB 4: ROI ANALYSIS
    with tab4:
        st.header("ROI & Efficiency Analysis")

        st.info("💡 Note: ROI calculation requires promo cost data. Add cost as parameter below.")

        # Promo cost input
        promo_cost = st.number_input(
            "Enter Total Promo Cost ($)",
            min_value=0.0,
            value=50000.0,
            step=1000.0,
            help="Total cost of promo (discounts, subsidies, etc.)"
        )

        if promo_cost > 0:
            roi = ((total_incremental_gmv - promo_cost) / promo_cost) * 100
            cost_per_dollar = promo_cost / total_incremental_gmv if total_incremental_gmv > 0 else 0

            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric(
                    "ROI %",
                    f"{roi:.1f}%",
                    delta="Return on Investment"
                )

            with col2:
                st.metric(
                    "Cost per $1 Incremental GMV",
                    f"${cost_per_dollar:.2f}"
                )

            with col3:
                net_benefit = total_incremental_gmv - promo_cost
                st.metric(
                    "Net Benefit",
                    f"${net_benefit:,.0f}"
                )

            # ROI waterfall
            st.subheader("ROI Waterfall")

            waterfall_data = pd.DataFrame({
                'Measure': ['Promo Cost', 'Incremental GMV', 'Net Benefit'],
                'Value': [-promo_cost, total_incremental_gmv, net_benefit],
                'Type': ['relative', 'relative', 'total']
            })

            fig = go.Figure(go.Waterfall(
                measure=waterfall_data['Type'],
                x=waterfall_data['Measure'],
                y=waterfall_data['Value'],
                connector={"line": {"color": "rgb(63, 63, 63)"}},
                decreasing={"marker": {"color": "#e74c3c"}},
                increasing={"marker": {"color": "#2ecc71"}},
                totals={"marker": {"color": "#3498db"}}
            ))
            fig.update_layout(height=400)
            st.plotly_chart(fig, width='stretch')

        # Efficiency by cohort
        st.subheader("Efficiency by Seller Cohort")

        efficiency = filtered_df.groupby('seller_size_cohort').agg({
            'incremental_gmv_usd': 'sum',
            'slr_id': 'nunique'
        }).reset_index()
        efficiency['GMV per Seller'] = efficiency['incremental_gmv_usd'] / efficiency['slr_id']
        efficiency.columns = ['Cohort', 'Total Incremental GMV', 'Num Sellers', 'GMV per Seller']

        fig = px.bar(
            efficiency,
            x='Cohort',
            y='GMV per Seller',
            color='Num Sellers',
            text='GMV per Seller',
            labels={'GMV per Seller': 'Avg Incremental GMV per Seller ($)'}
        )
        fig.update_traces(texttemplate='$%{text:,.0f}', textposition='outside')
        fig.update_layout(height=400)
        st.plotly_chart(fig, width="stretch")

    # TAB 5: PROMO COMPARISON (only if comparison is enabled)
    if tab5 and enable_comparison and compare_promo and compare_df is not None:
        with tab5:
            st.header(f"Comparing: {selected_promo} vs {compare_promo}")

            # Side-by-side KPIs
            col1, col2 = st.columns(2)

            with col1:
                st.subheader(f"🎯 {selected_promo}")
                promo1_gmv = filtered_df['incremental_gmv_usd'].sum()
                promo1_lift = filtered_df['gmv_lift_pct'].mean()
                promo1_sellers = filtered_df['slr_id'].nunique()

                st.metric("Incremental GMV", f"${promo1_gmv:,.0f}")
                st.metric("Avg GMV Lift %", f"{promo1_lift:.1f}%")
                st.metric("# Sellers", f"{promo1_sellers:,}")

            with col2:
                st.subheader(f"🎯 {compare_promo}")
                promo2_gmv = compare_df['incremental_gmv_usd'].sum()
                promo2_lift = compare_df['gmv_lift_pct'].mean()
                promo2_sellers = compare_df['slr_id'].nunique()

                delta_gmv = ((promo1_gmv - promo2_gmv) / promo2_gmv * 100) if promo2_gmv > 0 else 0
                delta_lift = promo1_lift - promo2_lift

                st.metric("Incremental GMV", f"${promo2_gmv:,.0f}",
                         delta=f"{delta_gmv:+.1f}% vs {selected_promo}")
                st.metric("Avg GMV Lift %", f"{promo2_lift:.1f}%",
                         delta=f"{delta_lift:+.1f}pp vs {selected_promo}")
                st.metric("# Sellers", f"{promo2_sellers:,}")

            st.markdown("---")

            # Side-by-side comparison charts
            st.subheader("Performance Comparison")

            # Prepare comparison data
            comparison_data = pd.DataFrame({
                'Promo': [selected_promo, compare_promo],
                'Incremental GMV': [promo1_gmv, promo2_gmv],
                'Avg Lift %': [promo1_lift, promo2_lift],
                'Sellers': [promo1_sellers, promo2_sellers],
                'GMV per Seller': [
                    promo1_gmv / promo1_sellers if promo1_sellers > 0 else 0,
                    promo2_gmv / promo2_sellers if promo2_sellers > 0 else 0
                ]
            })

            col1, col2 = st.columns(2)

            with col1:
                fig = px.bar(
                    comparison_data,
                    x='Promo',
                    y='Incremental GMV',
                    color='Promo',
                    text='Incremental GMV',
                    color_discrete_sequence=['#3498db', '#e74c3c']
                )
                fig.update_traces(texttemplate='$%{text:,.0f}', textposition='outside')
                fig.update_layout(height=400, showlegend=False)
                st.plotly_chart(fig, width="stretch")

            with col2:
                fig = px.bar(
                    comparison_data,
                    x='Promo',
                    y='Avg Lift %',
                    color='Promo',
                    text='Avg Lift %',
                    color_discrete_sequence=['#3498db', '#e74c3c']
                )
                fig.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
                fig.update_layout(height=400, showlegend=False)
                st.plotly_chart(fig, width="stretch")

            # Detailed comparison table
            st.subheader("Detailed Metrics Comparison")

            comparison_table = pd.DataFrame({
                'Metric': ['Incremental GMV', 'Avg Lift %', 'Number of Sellers',
                          'GMV per Seller', 'Total Incremental Revenue'],
                selected_promo: [
                    f"${promo1_gmv:,.0f}",
                    f"{promo1_lift:.1f}%",
                    f"{promo1_sellers:,}",
                    f"${promo1_gmv / promo1_sellers:,.0f}" if promo1_sellers > 0 else "$0",
                    f"${filtered_df['incremental_revenue_usd'].sum():,.0f}"
                ],
                compare_promo: [
                    f"${promo2_gmv:,.0f}",
                    f"{promo2_lift:.1f}%",
                    f"{promo2_sellers:,}",
                    f"${promo2_gmv / promo2_sellers:,.0f}" if promo2_sellers > 0 else "$0",
                    f"${compare_df['incremental_revenue_usd'].sum():,.0f}"
                ],
                'Difference': [
                    f"${promo1_gmv - promo2_gmv:+,.0f}",
                    f"{promo1_lift - promo2_lift:+.1f}pp",
                    f"{promo1_sellers - promo2_sellers:+,}",
                    f"${(promo1_gmv / promo1_sellers if promo1_sellers > 0 else 0) - (promo2_gmv / promo2_sellers if promo2_sellers > 0 else 0):+,.0f}",
                    f"${filtered_df['incremental_revenue_usd'].sum() - compare_df['incremental_revenue_usd'].sum():+,.0f}"
                ]
            })

            st.dataframe(comparison_table, width="stretch", hide_index=True)

    # Footer
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #7f8c8d;'>
        <p>Seller Promo Incrementality Dashboard | eBay Analytics Team | Last Updated: {}</p>
    </div>
    """.format(datetime.now().strftime('%Y-%m-%d %H:%M')), unsafe_allow_html=True)

if __name__ == "__main__":
    main()
