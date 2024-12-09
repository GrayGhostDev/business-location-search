import streamlit as st
import pandas as pd
from datetime import datetime
import os
from dotenv import load_dotenv
from api_integrations import collect_business_data
from database import DatabaseManager
from utils import clean_data, process_data, classify_address
from visualizations import create_map, create_charts
import plotly.express as px

# Load environment variables
load_dotenv()

# Page configuration
st.set_page_config(page_title="Incubizo Data Profiling", layout="wide")
st.title("Incubizo Data Profiling")

# Initialize database
@st.cache_resource
def get_database():
    return DatabaseManager()  # Using default SQLite configuration

db = get_database()

def clear_all():
    """Clear all session state and form values"""
    # Clear all session state
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    
    # Reset form values
    if 'primary_category' in st.session_state:
        del st.session_state.primary_category
    if 'selected_subcategories' in st.session_state:
        del st.session_state.selected_subcategories
    if 'related_categories' in st.session_state:
        del st.session_state.related_categories
    if 'location' in st.session_state:
        del st.session_state.location

# Sidebar for data collection
with st.sidebar:
    # Add clear button at the top
    if st.button("🔄 Clear All", type="secondary", help="Reset all fields and clear data"):
        clear_all()
        st.experimental_rerun()
    
    st.header("Data Collection")
    
    # API Selection
    st.subheader("API Configuration")
    api_type = st.selectbox(
        "Select API Source",
        ["here", "yelp"],
        help="Choose which API to use for data collection",
        key='api_type'
    )
    
    # API Keys
    if api_type == "here":
        api_key = st.text_input("HERE API Key", type="password", value=os.getenv('HERE_API_KEY', ''))
        if api_key:
            os.environ['HERE_API_KEY'] = api_key
    elif api_type == "yelp":
        api_key = st.text_input("Yelp API Key", type="password", value=os.getenv('YELP_API_KEY', ''))
        if api_key:
            os.environ['YELP_API_KEY'] = api_key
    
    # Updated Business Categories Section
    st.subheader("Business Categories")
    
    # Primary category as free text input
    primary_category = st.text_input(
        "Primary Business Category",
        value="",
        help="Enter the main type of business you want to search for (e.g., Restaurant, Law Firm, Auto Repair)",
        key='primary_category',
        placeholder="Enter primary business category"
    )
    
    # Additional categories as free text inputs
    st.markdown("### Additional Categories")
    st.markdown("Add up to 4 additional search categories to broaden your results")
    
    additional_categories = []
    for i in range(4):
        category = st.text_input(
            f"Additional Category {i+1}",
            value="",
            key=f'additional_category_{i}',
            placeholder=f"Enter additional category {i+1}"
        )
        if category:
            additional_categories.append(category)
    
    # Show current search categories
    if primary_category or additional_categories:
        st.markdown("### Current Search Categories")
        all_categories = [cat for cat in [primary_category] + additional_categories if cat]
        for idx, cat in enumerate(all_categories, 1):
            st.markdown(f"{idx}. {cat}")
    
    # Location input
    st.subheader("Location")
    location = st.text_input(
        "Search Location",
        value="",
        help="Enter city and state (e.g., Detroit, MI) or full address",
        key='location',
        placeholder="Enter location"
    )
    
    # Search radius
    radius = st.slider(
        "Search Radius (miles)",
        min_value=1,
        max_value=25,
        value=5,
        help="Select the search radius in miles"
    )
    
    # Convert radius to meters for API
    radius_meters = radius * 1609
    
    # Combine all categories for search
    search_categories = [cat for cat in [primary_category] + additional_categories if cat]
    
    # Data Collection Button
    if st.button("Collect Data", type="primary"):
        if not primary_category:
            st.error("Please enter a primary business category.")
        elif not location:
            st.error("Please enter a location.")
        else:
            with st.spinner(f"Collecting data for selected categories in {location}..."):
                try:
                    if api_key:
                        # Clear existing data
                        if 'data' in st.session_state:
                            del st.session_state.data
                        
                        # Collect data for each category
                        all_results = []
                        total_categories = len(search_categories)
                        
                        # Create a progress message
                        progress_text = st.empty()
                        
                        for idx, category in enumerate(search_categories, 1):
                            progress_text.text(f"Searching category {idx}/{total_categories}: {category}")
                            raw_data = collect_business_data(api_type, category, location)
                            if raw_data:
                                all_results.extend(raw_data)
                        
                        if all_results:
                            # Clean and process the combined data
                            progress_text.text("Processing collected data...")
                            cleaned_data = clean_data(all_results)
                            processed_data = process_data(cleaned_data)
                            
                            # Add category information
                            processed_data['Primary Category'] = primary_category
                            processed_data['Search Category'] = processed_data['Business Type']
                            
                            if not processed_data.empty:
                                # Store in session state
                                st.session_state.data = processed_data
                                # Save to database
                                db.save_businesses(processed_data.to_dict('records'))
                                
                                # Clear progress message
                                progress_text.empty()
                                
                                # Show success message and category breakdown
                                st.success(f"Found {len(processed_data)} businesses across {len(search_categories)} categories!")
                                
                                # Show category breakdown
                                category_counts = processed_data['Search Category'].value_counts()
                                st.markdown("### Results by Category:")
                                for cat, count in category_counts.items():
                                    st.markdown(f"- {cat}: {count} businesses")
                            else:
                                progress_text.empty()
                                st.error("Error processing the collected data.")
                        else:
                            progress_text.empty()
                            st.error(f"No businesses found in {location} for the selected categories.")
                    else:
                        st.error(f"Please enter your {api_type.title()} API key.")
                except Exception as e:
                    st.error(f"Error collecting data: {str(e)}")

# Main content area
st.header("Business Data")

# Get data from session state or start empty
if 'data' in st.session_state:
    df = st.session_state.data
else:
    df = pd.DataFrame()

# Only show data and visualizations if we have data
if not df.empty:
    # Add a clear results button in the main area
    col1, col2 = st.columns([1, 5])
    with col1:
        if st.button("🗑️ Clear Results", help="Clear all results and reset form fields"):
            clear_all()
            st.experimental_rerun()
    
    # Filter controls
    st.subheader("Filter Results")
    
    # Location filter
    available_locations = sorted(df['Address'].str.extract(r'([\w\s]+,\s*\w{2})')[0].unique())
    selected_location = st.multiselect(
        "Filter by Location",
        options=available_locations,
        default=available_locations,
        help="Select specific locations to display"
    )
    
    # Category filter
    available_categories = sorted(df['Search Category'].unique())
    selected_categories = st.multiselect(
        "Filter by Category",
        options=available_categories,
        default=available_categories,
        help="Select specific categories to display"
    )
    
    # Apply filters
    filtered_df = df[
        (df['Address'].str.extract(r'([\w\s]+,\s*\w{2})')[0].isin(selected_location)) &
        (df['Search Category'].isin(selected_categories))
    ]
    
    # Show results count
    if not filtered_df.empty:
        st.success(f"Found {len(filtered_df)} available listings")
        
        # Category breakdown
        st.subheader("Available Listings by Category")
        category_counts = filtered_df['Search Category'].value_counts()
        
        # Display category breakdown as a horizontal bar chart
        fig = px.bar(
            x=category_counts.values,
            y=category_counts.index,
            orientation='h',
            title="Number of Listings by Category"
        )
        fig.update_layout(
            xaxis_title="Number of Listings",
            yaxis_title="Category",
            showlegend=False
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Display the filtered data
        st.subheader("Available Listings")
        st.dataframe(
            filtered_df,
            column_config={
                "Business Name": st.column_config.TextColumn(
                    "Business Name",
                    width="large"
                ),
                "Address": st.column_config.TextColumn(
                    "Address",
                    width="large"
                ),
                "Phone": st.column_config.TextColumn(
                    "Phone",
                    width="medium"
                ),
                "Website": st.column_config.LinkColumn(
                    "Website",
                    width="medium"
                ),
                "Rating": st.column_config.NumberColumn(
                    "Rating",
                    format="%.1f ⭐",
                    width="small"
                ),
                "Reviews": st.column_config.NumberColumn(
                    "Reviews",
                    width="small"
                ),
                "Search Category": st.column_config.TextColumn(
                    "Category",
                    width="medium"
                )
            },
            hide_index=True
        )
        
        # Map visualization
        st.subheader("Locations Map")
        map_fig = create_map(filtered_df)
        if map_fig is not None:
            st.plotly_chart(map_fig, use_container_width=True)
        
        # Export options
        st.subheader("Export Results")
        if st.button("Download Results as CSV"):
            csv = filtered_df.to_csv(index=False)
            st.download_button(
                label="Click to Download",
                data=csv,
                file_name=f"business_listings_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
    else:
        st.warning("No listings found matching the selected filters.")
else:
    st.info("👈 Use the sidebar to start collecting business data.")
