#!/usr/bin/env python3
"""
Generates a JSON file of all counties for each state in the US.
"""

import json
import logging
import requests
import os
from collections import defaultdict

# Get the directory where this script is located
script_dir = os.path.dirname(os.path.abspath(__file__))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(script_dir, 'generate_counties.log'), encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def generate_counties_file():
    """
    Generates a JSON file containing all counties for each state.
    """
    logger.info("Starting to generate counties data...")
    
    url = "https://gist.githubusercontent.com/vitalii-z8i/bbb96d55d57f1e4342c3408e7286d3f2/raw/3b9b1fba8b226359d5a025221bb2688e9807c674/counties_list.json"
    
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()  # Raise an exception for bad status codes
        counties_list = response.json()
        
        # Convert the list to a dictionary of state: [counties] format
        counties_by_state = defaultdict(list)
        state_abbrevs = {
            'Alabama': 'AL', 'Alaska': 'AK', 'Arizona': 'AZ', 'Arkansas': 'AR', 
            'California': 'CA', 'Colorado': 'CO', 'Connecticut': 'CT', 'Delaware': 'DE',
            'Florida': 'FL', 'Georgia': 'GA', 'Hawaii': 'HI', 'Idaho': 'ID', 
            'Illinois': 'IL', 'Indiana': 'IN', 'Iowa': 'IA', 'Kansas': 'KS',
            'Kentucky': 'KY', 'Louisiana': 'LA', 'Maine': 'ME', 'Maryland': 'MD',
            'Massachusetts': 'MA', 'Michigan': 'MI', 'Minnesota': 'MN', 'Mississippi': 'MS',
            'Missouri': 'MO', 'Montana': 'MT', 'Nebraska': 'NE', 'Nevada': 'NV',
            'New Hampshire': 'NH', 'New Jersey': 'NJ', 'New Mexico': 'NM', 'New York': 'NY',
            'North Carolina': 'NC', 'North Dakota': 'ND', 'Ohio': 'OH', 'Oklahoma': 'OK',
            'Oregon': 'OR', 'Pennsylvania': 'PA', 'Rhode Island': 'RI', 'South Carolina': 'SC',
            'South Dakota': 'SD', 'Tennessee': 'TN', 'Texas': 'TX', 'Utah': 'UT',
            'Vermont': 'VT', 'Virginia': 'VA', 'Washington': 'WA', 'West Virginia': 'WV',
            'Wisconsin': 'WI', 'Wyoming': 'WY', 'District of Columbia': 'DC'
        }
        
        for county_data in counties_list:
            state_name = county_data['State']
            county_full = county_data['County']
            
            # Get state abbreviation
            state_abbrev = state_abbrevs.get(state_name)
            if not state_abbrev:
                logger.warning("Unknown state: %s", state_name)
                continue
                
            # Remove " County" suffix from county name
            county_name = county_full.replace(" County", "")
            
            # Add county to the list for the state
            counties_by_state[state_abbrev].append(county_name)
        
        # Sort counties alphabetically within each state
        for state_abbrev in counties_by_state:
            counties_by_state[state_abbrev].sort()
        
        logger.info("Processed %d counties across %d states", 
                   sum(len(counties) for counties in counties_by_state.values()),
                   len(counties_by_state))
                   
        # Check for specific counties we're interested in
        for state, counties in [('AR', ['Benton']), ('IN', ['Marshall'])]:
            for county in counties:
                if county in counties_by_state.get(state, []):
                    logger.info("Verified that %s County, %s is in the dataset", county, state)
                else:
                    logger.warning("%s County, %s is NOT in the dataset", county, state)
        
        # Convert defaultdict to regular dict for JSON serialization
        output_data = dict(counties_by_state)
        
        output_path = os.path.join(script_dir, 'counties.json')
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2)
        logger.info("Successfully created '%s' with county data in state:counties format.", output_path)
        
    except requests.exceptions.RequestException as e:
        logger.error("Failed to download county data: %s", e)
    except IOError as e:
        logger.error("Failed to write to %s: %s", output_path, e)

if __name__ == "__main__":
    generate_counties_file()
    logger.info("\nNext step: Run the discovery script to find Zuercher jails.")
    logger.info("python %s", os.path.join(script_dir, 'zuercher_discovery.py'))
