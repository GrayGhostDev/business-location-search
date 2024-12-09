import requests
from typing import List, Dict, Any, Optional, Union
import logging
import os
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GooglePlacesAPI:
    def __init__(self):
        self.api_key = os.getenv('GOOGLE_API_KEY')
        if not self.api_key:
            raise ValueError("Google API key not found in environment variables")
        
        self.base_url = "https://places.googleapis.com/v1/places"
    
    def search_businesses(self, query: str, location: str, radius: int = 5000) -> List[Dict]:
        """
        Search for businesses using Google Places API
        
        Args:
            query: Search term (e.g., "restaurants", "coffee shops")
            location: Location string (e.g., "New York, NY")
            radius: Search radius in meters (default 5000)
            
        Returns:
            List of business data dictionaries
        """
        try:
            # First, geocode the location
            geocode_url = f"https://maps.googleapis.com/maps/api/geocode/json"
            params = {
                'address': location,
                'key': self.api_key
            }
            
            geocode_response = requests.get(geocode_url, params=params)
            geocode_data = geocode_response.json()
            
            if not geocode_data.get('results'):
                logger.error(f"Could not geocode location: {location}")
                return []
            
            # Get coordinates from geocoding result
            location_data = geocode_data['results'][0]['geometry']['location']
            lat, lng = location_data['lat'], location_data['lng']
            
            # Search for businesses
            headers = {
                'Content-Type': 'application/json',
                'X-Goog-Api-Key': self.api_key,
                'X-Goog-FieldMask': 'places.displayName,places.formattedAddress,places.internationalPhoneNumber,places.rating,places.userRatingCount,places.websiteUri,places.location'
            }
            
            data = {
                'textQuery': f"{query} in {location}",
                'locationBias': {
                    'circle': {
                        'center': {'latitude': lat, 'longitude': lng},
                        'radius': radius
                    }
                },
                'maxResultCount': 20
            }
            
            response = requests.post(f"{self.base_url}:searchText", headers=headers, json=data)
            places_data = response.json()
            
            # Process and format the results
            businesses = []
            for place in places_data.get('places', []):
                business_data = {
                    'Business Name': place.get('displayName', {}).get('text', ''),
                    'Address': place.get('formattedAddress', ''),
                    'Phone': place.get('internationalPhoneNumber', ''),
                    'Rating': place.get('rating', 0.0),
                    'Review Count': place.get('userRatingCount', 0),
                    'Website': place.get('websiteUri', ''),
                    'Business Type': query,
                    'Location': {
                        'lat': place.get('location', {}).get('latitude', 0),
                        'lng': place.get('location', {}).get('longitude', 0)
                    }
                }
                businesses.append(business_data)
            
            return businesses
            
        except Exception as e:
            logger.error(f"Error searching businesses: {str(e)}")
            return []
    
    def get_business_details(self, place_id: str) -> Optional[Dict]:
        """
        Get detailed information about a specific business
        
        Args:
            place_id: Google Places ID for the business
            
        Returns:
            Dictionary containing business details or None if error occurs
        """
        try:
            headers = {
                'X-Goog-Api-Key': self.api_key,
                'X-Goog-FieldMask': '*'
            }
            
            response = requests.get(f"{self.base_url}/{place_id}", headers=headers)
            data = response.json()
            
            details = {
                'Business Name': data.get('displayName', {}).get('text', ''),
                'Address': data.get('formattedAddress', ''),
                'Phone': data.get('internationalPhoneNumber', ''),
                'Website': data.get('websiteUri', ''),
                'Rating': data.get('rating', 0.0),
                'Review Count': data.get('userRatingCount', 0),
                'Price Level': data.get('priceLevel', ''),
                'Business Status': data.get('businessStatus', ''),
                'Types': data.get('types', []),
                'Hours': data.get('currentOpeningHours', {}).get('weekdayDescriptions', [])
            }
            
            return details
            
        except Exception as e:
            logger.error(f"Error getting business details: {str(e)}")
            return None

class HerePlacesAPI:
    def __init__(self):
        self.api_key = os.getenv('HERE_API_KEY')
        if not self.api_key:
            raise ValueError("HERE API key not found in environment variables")
        
        self.base_url = "https://discover.search.hereapi.com/v1"
    
    def search_businesses(self, query: str, location: str, radius: int = 5000) -> List[Dict]:
        """
        Search for businesses using HERE Places API
        
        Args:
            query: Search term (e.g., "restaurants", "coffee shops")
            location: Location string (e.g., "New York, NY")
            radius: Search radius in meters (default 5000)
            
        Returns:
            List of business data dictionaries
        """
        try:
            # First, geocode the location
            geocode_url = f"https://geocode.search.hereapi.com/v1/geocode"
            params = {
                'q': location,
                'apiKey': self.api_key
            }
            
            geocode_response = requests.get(geocode_url, params=params)
            geocode_data = geocode_response.json()
            
            if not geocode_data.get('items'):
                logger.error(f"Could not geocode location: {location}")
                return []
            
            # Get coordinates from geocoding result
            position = geocode_data['items'][0]['position']
            lat, lng = position['lat'], position['lng']
            
            # Search for businesses
            search_url = f"{self.base_url}/discover"
            params = {
                'apiKey': self.api_key,
                'q': query,
                'at': f"{lat},{lng}",
                'limit': 20,
                'radius': radius
            }
            
            response = requests.get(search_url, params=params)
            data = response.json()
            
            # Process and format the results
            businesses = []
            for item in data.get('items', []):
                # Extract phone and website from contacts if available
                contacts = item.get('contacts', [{}])[0] if item.get('contacts') else {}
                phone = contacts.get('phone', [{}])[0].get('value', '') if contacts.get('phone') else ''
                website = contacts.get('www', [{}])[0].get('value', '') if contacts.get('www') else ''
                
                business_data = {
                    'Business Name': item.get('title', ''),
                    'Address': item.get('address', {}).get('label', ''),
                    'Phone': phone,
                    'Website': website,
                    'Business Type': query,
                    'Location': {
                        'lat': item.get('position', {}).get('lat', 0),
                        'lng': item.get('position', {}).get('lng', 0)
                    },
                    'Rating': 0.0,  # HERE API doesn't provide ratings
                    'Reviews': 0,    # HERE API doesn't provide review counts
                    'Categories': [cat.get('name', '') for cat in item.get('categories', [])],
                    'Distance': item.get('distance', 0),
                    'Source': 'HERE'
                }
                businesses.append(business_data)
            
            return businesses
            
        except Exception as e:
            logger.error(f"Error searching businesses with HERE API: {str(e)}")
            return []
    
    def get_business_details(self, place_id: str) -> Optional[Dict]:
        """
        Get detailed information about a specific business
        
        Args:
            place_id: HERE place ID
            
        Returns:
            Dictionary containing business details or None if error occurs
        """
        try:
            lookup_url = f"{self.base_url}/lookup"
            params = {
                'apiKey': self.api_key,
                'id': place_id
            }
            
            response = requests.get(lookup_url, params=params)
            data = response.json()
            
            if not data.get('items'):
                return None
            
            item = data['items'][0]
            details = {
                'Business Name': item.get('title', ''),
                'Address': item.get('address', {}).get('label', ''),
                'Phone': item.get('contacts', [{}])[0].get('phone', [{}])[0].get('value', '') if item.get('contacts') else '',
                'Website': item.get('contacts', [{}])[0].get('www', [{}])[0].get('value', '') if item.get('contacts') else '',
                'Categories': [cat.get('name') for cat in item.get('categories', [])],
                'OpeningHours': item.get('openingHours', {}).get('text', []) if item.get('openingHours') else [],
                'Location': {
                    'lat': item.get('position', {}).get('lat', 0),
                    'lng': item.get('position', {}).get('lng', 0)
                }
            }
            
            return details
            
        except Exception as e:
            logger.error(f"Error getting business details with HERE API: {str(e)}")
            return None

class YelpAPI:
    def __init__(self):
        self.api_key = os.getenv('YELP_API_KEY')
        if not self.api_key:
            raise ValueError("Yelp API key not found in environment variables")
        
        self.base_url = "https://api.yelp.com/v3"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "accept": "application/json"
        }
    
    def search_businesses(self, query: str, location: str, radius: int = 5000) -> List[Dict]:
        """
        Search for businesses using Yelp API
        
        Args:
            query: Search term (e.g., "restaurants", "coffee shops")
            location: Location string (e.g., "New York, NY")
            radius: Search radius in meters (default 5000)
            
        Returns:
            List of business data dictionaries
        """
        try:
            search_url = f"{self.base_url}/businesses/search"
            params = {
                'term': query,
                'location': location,
                'radius': radius,
                'limit': 50
            }
            
            response = requests.get(search_url, headers=self.headers, params=params)
            response.raise_for_status()
            data = response.json()
            
            businesses = []
            for business in data.get('businesses', []):
                business_data = {
                    'Business Name': business.get('name', ''),
                    'Address': ' '.join(business.get('location', {}).get('display_address', [])),
                    'Phone': business.get('phone', ''),
                    'Rating': business.get('rating', 0.0),
                    'Review Count': business.get('review_count', 0),
                    'Website': business.get('url', ''),
                    'Business Type': query,
                    'Location': {
                        'lat': business.get('coordinates', {}).get('latitude', 0),
                        'lng': business.get('coordinates', {}).get('longitude', 0)
                    },
                    'Price': business.get('price', ''),
                    'Categories': [cat.get('title') for cat in business.get('categories', [])],
                    'Source': 'Yelp'
                }
                businesses.append(business_data)
            
            return businesses
            
        except Exception as e:
            logger.error(f"Error searching businesses with Yelp API: {str(e)}")
            return []

def collect_business_data(api_type: str, business_type: str, location: str) -> List[Dict]:
    """
    Collect business data from selected API source
    
    Args:
        api_type: Type of API to use ('here' or 'yelp')
        business_type: Type of business to search for
        location: Location to search in
        
    Returns:
        List of business data dictionaries
    """
    try:
        results = []
        
        if api_type == 'here' and os.getenv('HERE_API_KEY'):
            api = HerePlacesAPI()
            results = api.search_businesses(business_type, location)
            
        elif api_type == 'yelp' and os.getenv('YELP_API_KEY'):
            api = YelpAPI()
            results = api.search_businesses(business_type, location)
            
        return results
        
    except Exception as e:
        logger.error(f"Error collecting business data: {str(e)}")
        raise
