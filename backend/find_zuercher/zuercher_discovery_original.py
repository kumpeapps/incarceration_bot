#!/usr/bin/env python3
"""
Zuercher Portal Discovery System
Identifies all jails that use Zuercher Portal by testing county URLs across all US states.
"""

import requests
import json
import csv
import logging
import os
from typing import List, Dict, Tuple, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
import urllib3

# Disable SSL warnings for testing purposes
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Configure logging with environment variable support
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
log_level = getattr(logging, LOG_LEVEL, logging.INFO)

logging.basicConfig(
    level=log_level,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('zuercher_discovery.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ZuercherDiscovery:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        self.valid_jails = []
        self.tested_count = 0
        self.total_count = 0
        
    def load_counties_data(self) -> Dict[str, List[str]]:
        """Load county data from the counties.json file"""
        import os
        from collections import defaultdict
        
        # Get the directory where this script is located
        script_dir = os.path.dirname(os.path.abspath(__file__))
        counties_path = os.path.join(script_dir, 'counties.json')
        
        try:
            with open(counties_path, 'r', encoding='utf-8') as f:
                counties_list = json.load(f)
                
            # Convert the list of counties to a dictionary organized by state
            counties_by_state = defaultdict(list)
            
            for county_entry in counties_list:
                state_name = county_entry.get("State")
                county_name = county_entry.get("County")
                
                if state_name and county_name:
                    # Extract state abbreviation - assuming this is needed
                    state_abbrev = self.get_state_abbreviation(state_name)
                    
                    # Remove " County" suffix if present
                    if " County" in county_name:
                        county_name = county_name.replace(" County", "")
                    
                    counties_by_state[state_abbrev].append(county_name)
            
            return dict(counties_by_state)
                
        except FileNotFoundError:
            logger.error("counties.json file not found at %s. Please run generate_counties.py first.", counties_path)
            return {}
        except (json.JSONDecodeError, IOError) as e:
            logger.error("Error reading counties.json: %s", e)
            return {}
            
    def get_state_abbreviation(self, state_name: str) -> str:
        """Get the two-letter abbreviation for a state name"""
        state_abbrevs = {
            "Alabama": "AL", "Alaska": "AK", "Arizona": "AZ", "Arkansas": "AR", 
            "California": "CA", "Colorado": "CO", "Connecticut": "CT", "Delaware": "DE",
            "Florida": "FL", "Georgia": "GA", "Hawaii": "HI", "Idaho": "ID", 
            "Illinois": "IL", "Indiana": "IN", "Iowa": "IA", "Kansas": "KS",
            "Kentucky": "KY", "Louisiana": "LA", "Maine": "ME", "Maryland": "MD", 
            "Massachusetts": "MA", "Michigan": "MI", "Minnesota": "MN", "Mississippi": "MS",
            "Missouri": "MO", "Montana": "MT", "Nebraska": "NE", "Nevada": "NV", 
            "New Hampshire": "NH", "New Jersey": "NJ", "New Mexico": "NM", "New York": "NY",
            "North Carolina": "NC", "North Dakota": "ND", "Ohio": "OH", "Oklahoma": "OK", 
            "Oregon": "OR", "Pennsylvania": "PA", "Rhode Island": "RI", "South Carolina": "SC",
            "South Dakota": "SD", "Tennessee": "TN", "Texas": "TX", "Utah": "UT", 
            "Vermont": "VT", "Virginia": "VA", "Washington": "WA", "West Virginia": "WV",
            "Wisconsin": "WI", "Wyoming": "WY", "District of Columbia": "DC"
        }
        
        return state_abbrevs.get(state_name, state_name[:2].upper())
    
    def normalize_county_name(self, county_name: str) -> str:
        """
        Normalize county name for URL construction
        - Remove 'County' suffix
        - Replace spaces with hyphens
        - Convert to lowercase
        - Handle special characters
        """
        # Remove common suffixes
        suffixes_to_remove = [' County', ' Parish', ' Borough', ' City and County', ' City', ' Municipality']
        normalized = county_name
        
        for suffix in suffixes_to_remove:
            if normalized.endswith(suffix):
                normalized = normalized[:-len(suffix)]
                break
        
        # Handle special cases
        special_cases = {
            'St.': 'saint',
            'St ': 'saint-',
            'Ste.': 'sainte',
            'Ste ': 'sainte-',
            'DeKalb': 'dekalb',
            'DuPage': 'dupage',
            'LaSalle': 'lasalle',
            'LaPorte': 'laporte',
            'McLean': 'mclean',
            'McHenry': 'mchenry',
            'O\'Brien': 'obrien',
            'Prince George\'s': 'prince-georges',
        }
        
        for old, new in special_cases.items():
            normalized = normalized.replace(old, new)
        
        # Replace spaces and special characters with hyphens
        normalized = normalized.replace(' ', '-')
        normalized = normalized.replace('\'', '')
        normalized = normalized.replace('.', '')
        normalized = normalized.replace('&', 'and')
        
        # Convert to lowercase and remove multiple hyphens
        normalized = normalized.lower()
        while '--' in normalized:
            normalized = normalized.replace('--', '-')
        
        # Remove leading/trailing hyphens
        normalized = normalized.strip('-')
        
        return normalized
    
    def construct_url(self, county: str, state_abbrev: str) -> str:
        """Construct the Zuercher Portal URL for a county"""
        normalized_county = self.normalize_county_name(county)
        return f"https://{normalized_county}-so-{state_abbrev.lower()}.zuercherportal.com/#/"
    
    def test_url(self, url: str, county: str, state: str, state_abbrev: str) -> Tuple[bool, Dict]:
        """Test if a Zuercher Portal URL is valid"""
        try:
            # Use a shorter timeout and disable SSL verification for speed
            response = self.session.get(
                url, 
                timeout=10, 
                verify=False, 
                allow_redirects=True,
                stream=True
            )
            
            # Check if we get a valid response
            if response.status_code == 200:
                # Check if it's actually a Zuercher portal (not a generic landing page)
                content_sample = response.text[:2000].lower()
                
                # Look for Zuercher-specific indicators
                zuercher_indicators = [
                    'zuercher',
                    'inmate roster',
                    'jail roster',
                    'booking',
                    'detention',
                    'sheriff'
                ]
                
                # Must have at least one indicator to be considered valid
                has_indicators = any(indicator in content_sample for indicator in zuercher_indicators)
                
                if has_indicators:
                    jail_info = {
                        'county': county,
                        'state': state,
                        'state_abbrev': state_abbrev,
                        'url': url,
                        'jail_name': f"{county} County {state_abbrev} Jail",
                        'jail_id': f"{self.normalize_county_name(county)}-so-{state_abbrev.lower()}",
                        'scrape_system': 'zuercherportal',
                        'discovered_date': datetime.now().strftime('%Y-%m-%d'),
                        'status_code': response.status_code
                    }
                    logger.info("✓ Valid Zuercher Portal found: %s, %s - %s", county, state_abbrev, url)
                    return True, jail_info
                else:
                    logger.debug("✗ URL responds but no Zuercher indicators: %s, %s - %s", county, state_abbrev, url)
                    return False, {}
            else:
                logger.debug("✗ HTTP %s: %s, %s - %s", response.status_code, county, state_abbrev, url)
                return False, {}
                
        except requests.exceptions.Timeout:
            logger.debug("✗ Timeout: %s, %s - %s", county, state_abbrev, url)
            return False, {}
        except requests.exceptions.ConnectionError:
            logger.debug("✗ Connection error: %s, %s - %s", county, state_abbrev, url)
            return False, {}
        except requests.exceptions.RequestException as e:
            logger.debug("✗ Request error for %s, %s: %s", county, state_abbrev, e)
            return False, {}
        except (ValueError, KeyError, AttributeError) as e:
            logger.error("✗ Unexpected error for %s, %s: %s", county, state_abbrev, e)
            return False, {}
    
    def process_county(self, county: str, state: str, state_abbrev: str) -> Tuple[bool, Dict]:
        """Process a single county"""
        url = self.construct_url(county, state_abbrev)
        is_valid, jail_info = self.test_url(url, county, state, state_abbrev)
        
        self.tested_count += 1
        if self.tested_count % 100 == 0:
            logger.info("Progress: %d/%d tested, %d valid jails found", 
                       self.tested_count, self.total_count, len(self.valid_jails))
        
        if is_valid:
            return True, jail_info
        return False, {}
    
    def discover_zuercher_jails(self, max_workers: int = 20):
        """Main method to discover all Zuercher Portal jails"""
        logger.info("Starting Zuercher Portal discovery...")
        
        # Load counties data
        counties_data = self.load_counties_data()
        if not counties_data:
            logger.error("No counties data available. Exiting.")
            return
        
        # Calculate total counties to test
        self.total_count = sum(len(counties) for counties in counties_data.values())
        logger.info("Total counties to test: %d", self.total_count)
        
        # Create tasks for all counties
        tasks = []
        for state_abbrev, counties in counties_data.items():
            # Get full state name (you might want to add a state mapping)
            state_name = state_abbrev  # Simplified for now
            for county in counties:
                tasks.append((county, state_name, state_abbrev))
        
        # Process counties with threading
        logger.info("Starting discovery with %d workers...", max_workers)
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all tasks
            future_to_county = {
                executor.submit(self.process_county, county, state, state_abbrev): (county, state, state_abbrev)
                for county, state, state_abbrev in tasks
            }
            
            # Process completed tasks
            for future in as_completed(future_to_county):
                try:
                    is_valid, jail_info = future.result()
                    if is_valid:
                        self.valid_jails.append(jail_info)
                except (ValueError, KeyError, RuntimeError) as e:
                    county, state, state_abbrev = future_to_county[future]
                    logger.error("Error processing %s, %s: %s", county, state_abbrev, e)
        
        logger.info("Discovery complete! Found %d valid Zuercher Portal jails", len(self.valid_jails))
        
        # Save results
        self.save_results()
    
    def save_results(self):
        """Save discovered jails to various formats"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Save as JSON
        json_filename = f'zuercher_jails_{timestamp}.json'
        with open(json_filename, 'w', encoding='utf-8') as f:
            json.dump(self.valid_jails, f, indent=2)
        logger.info("Results saved to %s", json_filename)
        
        # Save as text file (simple list)
        txt_filename = f'zuercher_jails_{timestamp}.txt'
        with open(txt_filename, 'w', encoding='utf-8') as f:
            f.write(f"Zuercher Portal Jails Discovered - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Total jails found: {len(self.valid_jails)}\n\n")
            
            for jail in sorted(self.valid_jails, key=lambda x: (x['state_abbrev'], x['county'])):
                f.write(f"{jail['jail_name']}\n")
                f.write(f"  URL: {jail['url']}\n")
                f.write(f"  Jail ID: {jail['jail_id']}\n")
                f.write(f"  State: {jail['state_abbrev']}\n\n")
        
        logger.info("Text summary saved to %s", txt_filename)
        
        # Save as CSV
        csv_filename = f'zuercher_jails_{timestamp}.csv'
        with open(csv_filename, 'w', newline='', encoding='utf-8') as f:
            if self.valid_jails:
                writer = csv.DictWriter(f, fieldnames=self.valid_jails[0].keys())
                writer.writeheader()
                writer.writerows(self.valid_jails)
        logger.info("CSV data saved to %s", csv_filename)
        
        # Save latest as simple names too
        with open('zuercher_jails_latest.json', 'w', encoding='utf-8') as f:
            json.dump(self.valid_jails, f, indent=2)
        
        with open('zuercher_jails_latest.txt', 'w', encoding='utf-8') as f:
            f.write(f"Zuercher Portal Jails Discovered - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Total jails found: {len(self.valid_jails)}\n\n")
            
            for jail in sorted(self.valid_jails, key=lambda x: (x['state_abbrev'], x['county'])):
                f.write(f"{jail['jail_name']}\n")
                f.write(f"  URL: {jail['url']}\n")
                f.write(f"  Jail ID: {jail['jail_id']}\n")
                f.write(f"  State: {jail['state_abbrev']}\n\n")

def main():
    """Main function to run the discovery"""
    discovery = ZuercherDiscovery()
    discovery.discover_zuercher_jails(max_workers=20)

if __name__ == "__main__":
    main()
