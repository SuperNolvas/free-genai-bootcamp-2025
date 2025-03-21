from typing import Dict, Optional
import aiohttp
from fastapi import HTTPException
from ..core.config import get_settings

settings = get_settings()

class GooglePlacesService:
    def __init__(self):
        self.api_key = settings.GOOGLE_PLACES_API_KEY
        if not self.api_key:
            raise ValueError("Google Places API key is not configured")

    async def reverse_geocode_location(self, lat: float, lon: float) -> Dict:
        """Get location details including Japanese place names using Google Places API
        
        Args:
            lat: Latitude in decimal degrees
            lon: Longitude in decimal degrees
            
        Returns:
            Dict containing address and location features
        """
        base_url = "https://maps.googleapis.com/maps/api/geocode/json"
        params = {
            'latlng': f"{lat},{lon}",
            'language': 'ja',  # Request Japanese results
            'key': self.api_key
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(base_url, params=params) as response:
                if response.status != 200:
                    raise HTTPException(
                        status_code=response.status,
                        detail="Google Places API request failed"
                    )
                data = await response.json()
                
                if data['status'] != 'OK':
                    raise HTTPException(
                        status_code=503,
                        detail=f"Google Places API error: {data['status']}"
                    )

                # Format the response
                result = data['results'][0] if data['results'] else {}
                address_components = result.get('address_components', [])
                
                # Extract components
                locality = next((c['long_name'] for c in address_components 
                               if 'locality' in c['types']), '')
                sublocality = next((c['long_name'] for c in address_components 
                                  if 'sublocality' in c['types']), '')
                neighborhood = next((c['long_name'] for c in address_components 
                                  if 'neighborhood' in c['types']), '')
                
                return {
                    'address': {
                        'Address': result.get('formatted_address', ''),
                        'Street': sublocality or neighborhood,
                        'Neighborhood': locality,
                        'District': '',
                        'LongLabel': result.get('formatted_address', ''),  # Japanese formatted address
                        'ShortLabel': locality or sublocality or neighborhood  # Shorter Japanese name
                    },
                    'features': []  # Google Places doesn't provide water features
                }