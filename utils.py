import pandas as pd
from typing import List, Dict, Tuple
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def classify_address(address: str) -> Tuple[str, str]:
    """
    Classify an address as residential or commercial
    
    Args:
        address: Address string to classify
        
    Returns:
        Tuple of (classification, color)
    """
    # Common commercial indicators
    commercial_indicators = [
        'suite', 'ste', 'unit', 'floor', 'fl', '#', 
        'plaza', 'mall', 'building', 'bldg', 'office',
        'commercial', 'industrial', 'shopping center',
        'retail', 'store', 'shop'
    ]
    
    address_lower = address.lower()
    
    # Check for commercial indicators
    is_commercial = any(indicator in address_lower for indicator in commercial_indicators)
    
    if is_commercial:
        return ('Commercial', '#FFD700')  # Yellow
    else:
        return ('Residential', '#90EE90')  # Light green

def clean_data(raw_data: List[Dict]) -> List[Dict]:
    """
    Clean and standardize the raw business data
    
    Args:
        raw_data: List of business dictionaries from API
        
    Returns:
        List of cleaned business dictionaries
    """
    cleaned_data = []
    
    for business in raw_data:
        try:
            address = business.get('Address', '')
            address_type, color = classify_address(address)
            
            cleaned_business = {
                'Business Name': business.get('Business Name', ''),
                'Address': address,
                'Address Type': address_type,
                'Address Color': color,
                'Phone': business.get('Phone', ''),
                'Rating': float(business.get('Rating', 0)),
                'Reviews': int(business.get('Review Count', 0)),
                'Website': business.get('Website', ''),
                'Business Type': business.get('Business Type', ''),
                'Location': business.get('Location', {'lat': 0, 'lng': 0}),
                'Source': business.get('Source', '')
            }
            cleaned_data.append(cleaned_business)
        except Exception as e:
            logger.error(f"Error cleaning business data: {str(e)}")
            continue
    
    return cleaned_data

def process_data(cleaned_data: List[Dict]) -> pd.DataFrame:
    """
    Process cleaned data into a pandas DataFrame
    
    Args:
        cleaned_data: List of cleaned business dictionaries
        
    Returns:
        Pandas DataFrame with processed business data
    """
    try:
        df = pd.DataFrame(cleaned_data)
        
        # Convert data types
        if 'Rating' in df.columns:
            df['Rating'] = pd.to_numeric(df['Rating'], errors='coerce')
        if 'Reviews' in df.columns:
            df['Reviews'] = pd.to_numeric(df['Reviews'], errors='coerce')
            
        # Fill missing values
        df = df.fillna({
            'Rating': 0,
            'Reviews': 0,
            'Website': '',
            'Phone': ''
        })
        
        return df
        
    except Exception as e:
        logger.error(f"Error processing data: {str(e)}")
        return pd.DataFrame()
