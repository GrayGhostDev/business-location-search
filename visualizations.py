import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import logging
from typing import Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_category_distribution(df: pd.DataFrame) -> go.Figure:
    """Create a bar chart showing number of businesses by category"""
    fig = px.bar(
        df['Business Type'].value_counts().reset_index(),
        x='index',
        y='Business Type',
        title='Number of Businesses by Category',
        labels={'index': 'Business Type', 'Business Type': 'Count'},
        color='index'
    )
    fig.update_layout(showlegend=False)
    return fig

def create_employee_distribution(df: pd.DataFrame) -> go.Figure:
    """Create a pie chart showing distribution of employee ranges"""
    employee_dist = df['Employees'].value_counts()
    fig = px.pie(
        values=employee_dist.values,
        names=employee_dist.index,
        title='Distribution of Employee Ranges',
        hole=0.3
    )
    return fig

def create_revenue_distribution(df: pd.DataFrame) -> go.Figure:
    """Create a treemap of revenue ranges"""
    revenue_dist = df['Revenue'].value_counts().reset_index()
    fig = px.treemap(
        revenue_dist,
        path=['index'],
        values='Revenue',
        title='Revenue Distribution'
    )
    return fig

def create_location_map(df: pd.DataFrame) -> go.Figure:
    """Create a map visualization of business locations"""
    # Note: This assumes we have latitude and longitude data
    if 'latitude' in df.columns and 'longitude' in df.columns:
        fig = px.scatter_mapbox(
            df,
            lat='latitude',
            lon='longitude',
            hover_name='Business Name',
            hover_data=['Business Type', 'Address'],
            color='Business Type',
            zoom=10,
            title='Business Locations'
        )
        fig.update_layout(mapbox_style='carto-positron')
        return fig
    return None

def create_ratings_histogram(df: pd.DataFrame) -> go.Figure:
    """Create a histogram of business ratings"""
    if 'Rating' in df.columns:
        fig = px.histogram(
            df,
            x='Rating',
            nbins=20,
            title='Distribution of Business Ratings',
            labels={'Rating': 'Rating', 'count': 'Number of Businesses'}
        )
        return fig
    return None

def calculate_key_metrics(df: pd.DataFrame) -> dict:
    """Calculate key business metrics"""
    metrics = {
        'Total Businesses': len(df),
        'Business Categories': df['Business Type'].nunique(),
        'Average Rating': round(df['Rating'].mean(), 2) if 'Rating' in df.columns else None,
        'Most Common Size': df['Employees'].mode().iloc[0] if not df['Employees'].empty else None,
        'Top Revenue Range': df['Revenue'].mode().iloc[0] if not df['Revenue'].empty else None
    }
    return metrics

def create_time_series(df: pd.DataFrame) -> go.Figure:
    """Create a time series of business additions"""
    if 'created_at' in df.columns:
        df['created_at'] = pd.to_datetime(df['created_at'])
        time_series = df.groupby(df['created_at'].dt.date).size().reset_index()
        fig = px.line(
            time_series,
            x='created_at',
            y=0,
            title='Business Additions Over Time',
            labels={'created_at': 'Date', '0': 'Number of Businesses Added'}
        )
        return fig
    return None

def create_source_distribution(df: pd.DataFrame) -> go.Figure:
    """Create a donut chart showing distribution of data sources"""
    if 'Source' in df.columns:
        fig = px.pie(
            df['Source'].value_counts().reset_index(),
            values='Source',
            names='index',
            title='Data Source Distribution',
            hole=0.4
        )
        return fig
    return None

def create_map(df: pd.DataFrame) -> Optional[go.Figure]:
    """
    Create an interactive map with business locations
    """
    try:
        # Extract latitude and longitude from Location column
        lats = [loc.get('lat') for loc in df['Location']]
        lons = [loc.get('lng') for loc in df['Location']]
        
        # Create hover text
        hover_text = df.apply(
            lambda row: f"""
            <b>{row['Business Name']}</b><br>
            Address: {row['Address']}<br>
            Type: {row['Address Type']}<br>
            Rating: {row['Rating']:.1f} ({row['Reviews']} reviews)<br>
            Phone: {row['Phone']}<br>
            <a href="{row['Website']}" target="_blank">Website</a>
            """,
            axis=1
        )
        
        # Create the map
        fig = go.Figure()
        
        # Add business markers with colors based on address type
        fig.add_trace(go.Scattermapbox(
            lat=lats,
            lon=lons,
            mode='markers',
            marker=go.scattermapbox.Marker(
                size=12,
                color=df['Address Color'],
                showscale=False
            ),
            text=hover_text,
            hoverinfo='text',
            name='Businesses'
        ))
        
        # Update layout
        fig.update_layout(
            mapbox=dict(
                style='carto-positron',
                zoom=11,
                center=dict(
                    lat=sum(lats)/len(lats),
                    lon=sum(lons)/len(lons)
                )
            ),
            margin=dict(l=0, r=0, t=0, b=0),
            height=600,
            showlegend=False
        )
        
        return fig
        
    except Exception as e:
        print(f"Error creating map: {str(e)}")
        return None

def create_charts(df: pd.DataFrame, column: str) -> Optional[go.Figure]:
    """
    Create distribution charts for numeric columns
    
    Args:
        df: DataFrame containing business data
        column: Column name to visualize
        
    Returns:
        Plotly figure object with the chart
    """
    try:
        if column == "Rating":
            fig = px.histogram(
                df,
                x=column,
                nbins=10,
                title=f"{column} Distribution",
                color_discrete_sequence=['#3366cc']
            )
            fig.update_layout(
                xaxis_title=column,
                yaxis_title="Number of Businesses",
                bargap=0.1
            )
        else:  # Reviews
            fig = px.box(
                df,
                y=column,
                title=f"{column} Distribution",
                color_discrete_sequence=['#3366cc']
            )
            fig.update_layout(
                yaxis_title="Number of Reviews",
                showlegend=False
            )
        
        return fig
        
    except Exception as e:
        print(f"Error creating chart: {str(e)}")
        return None
