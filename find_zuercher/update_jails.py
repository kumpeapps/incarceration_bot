#!/usr/bin/env python3
import json
import os
import datetime
from collections import defaultdict

# Get the script directory
script_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(script_dir)

# Define file paths
zuercher_jails_file = os.path.join(script_dir, 'zuercher_jails_latest.json')
jails_json_file = os.path.join(root_dir, 'jails.json')
readme_file = os.path.join(root_dir, 'README.md')

# Current date in YYYY-MM-DD format
today = datetime.datetime.now().strftime('%Y-%m-%d')

def load_json_file(file_path):
    """Load a JSON file"""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_json_file(data, file_path):
    """Save data to a JSON file with pretty formatting"""
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)
        
def extract_state_name(state_code):
    """Convert state code to full state name"""
    state_names = {
        'AL': 'Alabama', 'AK': 'Alaska', 'AZ': 'Arizona', 'AR': 'Arkansas', 'CA': 'California',
        'CO': 'Colorado', 'CT': 'Connecticut', 'DE': 'Delaware', 'FL': 'Florida', 'GA': 'Georgia',
        'HI': 'Hawaii', 'ID': 'Idaho', 'IL': 'Illinois', 'IN': 'Indiana', 'IA': 'Iowa',
        'KS': 'Kansas', 'KY': 'Kentucky', 'LA': 'Louisiana', 'ME': 'Maine', 'MD': 'Maryland',
        'MA': 'Massachusetts', 'MI': 'Michigan', 'MN': 'Minnesota', 'MS': 'Mississippi', 'MO': 'Missouri',
        'MT': 'Montana', 'NE': 'Nebraska', 'NV': 'Nevada', 'NH': 'New Hampshire', 'NJ': 'New Jersey',
        'NM': 'New Mexico', 'NY': 'New York', 'NC': 'North Carolina', 'ND': 'North Dakota', 'OH': 'Ohio',
        'OK': 'Oklahoma', 'OR': 'Oregon', 'PA': 'Pennsylvania', 'RI': 'Rhode Island', 'SC': 'South Carolina',
        'SD': 'South Dakota', 'TN': 'Tennessee', 'TX': 'Texas', 'UT': 'Utah', 'VT': 'Vermont',
        'VA': 'Virginia', 'WA': 'Washington', 'WV': 'West Virginia', 'WI': 'Wisconsin', 'WY': 'Wyoming'
    }
    return state_names.get(state_code, state_code)

def update_jails_json():
    """Update jails.json with new Zuercher jails"""
    # Load data
    zuercher_jails = load_json_file(zuercher_jails_file)
    try:
        existing_jails = load_json_file(jails_json_file)
    except FileNotFoundError:
        existing_jails = []
    
    # Get existing jail IDs
    existing_jail_ids = set(jail['jail_id'] for jail in existing_jails)
    
    # Find the highest existing ID
    max_id = 0
    if existing_jails:
        max_id = max(jail['id'] for jail in existing_jails)
    
    # Add new jails
    added_count = 0
    for zuercher_jail in zuercher_jails:
        # Convert jail_id from "county-so-st" to "county-co-st" format to match existing convention
        jail_id = zuercher_jail['jail_id']
        if "-so-" in jail_id:
            jail_id = jail_id.replace("-so-", "-co-")
        
        if jail_id not in existing_jail_ids:
            max_id += 1
            new_jail = {
                'id': max_id,
                'jail_name': zuercher_jail['jail_name'],
                'state': zuercher_jail['state'],
                'jail_id': jail_id,  # Use the converted jail_id
                'scrape_system': zuercher_jail['scrape_system'],
                'active': True,
                'created_date': today,
                'updated_date': today,
                'last_scrape_date': None
            }
            existing_jails.append(new_jail)
            added_count += 1
    
    # Save updated jails
    if added_count > 0:
        save_json_file(existing_jails, jails_json_file)
        print(f"Added {added_count} new jails to jails.json")
    else:
        print("No new jails to add to jails.json")
    
    return existing_jails

def update_readme(jails):
    """Update README.md with the current jails table"""
    # Read the README
    with open(readme_file, 'r', encoding='utf-8') as f:
        readme_content = f.read()
    
    # Find the jails table section
    table_start = readme_content.find("### Current Jails")
    if table_start == -1:
        print("Cannot find 'Current Jails' section in README.md")
        return
    
    table_end = readme_content.find("###", table_start + 1)
    if table_end == -1:
        table_end = len(readme_content)
    
    # Keep the header but replace the table
    header_end = readme_content.find("|", table_start)
    if header_end == -1:
        print("Cannot find table header in README.md")
        return
    
    header = readme_content[table_start:header_end]
    
    # Extract existing version info from README
    existing_versions = {}
    existing_mugshots = {}
    
    # Extract data from original table
    table_section = readme_content[table_start:table_end]
    table_lines = table_section.strip().split('\n')
    for line in table_lines:
        if '|' in line and not line.startswith('|---') and not "State" in line:
            cells = [cell.strip() for cell in line.split('|')]
            if len(cells) >= 5:  # Valid row with enough columns
                try:
                    state = cells[1].strip()
                    county_full = cells[2].strip()
                    county = county_full.replace(" County", "")
                    jail_id = cells[3].strip()
                    version = cells[4].strip()
                    mugshot_info = cells[5].strip()
                    
                    existing_versions[jail_id] = version
                    existing_mugshots[jail_id] = mugshot_info
                except IndexError:
                    continue
    
    # Create a mapping of jails by state for sorting
    jails_by_state = defaultdict(list)
    processed_jail_ids = set()  # To avoid duplicates
    
    for jail in jails:
        state_code = jail['state']
        state_name = extract_state_name(state_code)
        
        # Extract county name from jail_name (format: "County County ST Jail")
        jail_name = jail['jail_name']
        county = jail_name.split(" County")[0]
        
        # Convert from "county-so-st" to "county-co-st" format to match README
        jail_id = jail['jail_id']
        if "-so-" in jail_id:
            jail_id = jail_id.replace("-so-", "-co-")
            
        # Skip if we've already processed this jail_id
        if jail_id in processed_jail_ids:
            continue
        processed_jail_ids.add(jail_id)
        
        # Use existing version and mugshot info if available
        version = existing_versions.get(jail_id, "3.0.0")  # Default to 3.0.0 for new jails
        mugshot = existing_mugshots.get(jail_id, ":white_check_mark:")  # Default to yes for new jails
        
        jails_by_state[state_name].append({
            'state': state_name,
            'county': county,
            'jail_id': jail_id,
            'version': version,
            'mugshot': mugshot
        })
    
    # Build the new table
    table = f"{header}\n"
    table += "| State    | Jail              | Jail ID          | Added In Version | Mugshot                     |\n"
    table += "|----------|-------------------|------------------|------------------|-----------------------------|"
    
    # Add rows sorted by state and then by county
    for state in sorted(jails_by_state.keys()):
        for jail in sorted(jails_by_state[state], key=lambda j: j['county']):
            county_display = f"{jail['county']} County"
            state_text = state.ljust(8)
            county_text = county_display.ljust(15)
            jail_id_text = jail['jail_id'].ljust(15)
            version_text = jail['version'].ljust(16)
            mugshot_text = jail['mugshot']
            
            table += f"\n| {state_text} | {county_text} | {jail_id_text} | {version_text} | {mugshot_text} |"
    
    # Replace the old table with the new one
    new_readme = readme_content[:table_start] + table + readme_content[table_end:]
    
    # Write the updated README
    with open(readme_file, 'w', encoding='utf-8') as f:
        f.write(new_readme)
    
    print("Updated README.md with current jails table")
    
    # Build the new table
    table = f"{header}\n"
    table += "| State    | Jail              | Jail ID          | Added In Version | Mugshot                     |\n"
    table += "|----------|-------------------|------------------|------------------|-----------------------------|"
    
    # Add rows sorted by state and then by county
    for state in sorted(jails_by_state.keys()):
        for jail in sorted(jails_by_state[state], key=lambda j: j['county']):
            county_padded = jail['county'].ljust(15)
            jail_id_padded = jail['jail_id'].ljust(15)
            version = jail['version']
            mugshot_text = ":white_check_mark:" if jail['mugshot'] else ":x:"
            
            table += f"\n| {state.ljust(8)} | {county_padded} | {jail_id_padded} | {version.ljust(16)} | {mugshot_text.ljust(20)} |"
    
    # Replace the old table with the new one
    new_readme = readme_content[:table_start] + table + readme_content[table_end:]
    
    # Write the updated README
    with open(readme_file, 'w', encoding='utf-8') as f:
        f.write(new_readme)
    
    print("Updated README.md with current jails table")

def main():
    print("Updating jails.json with new Zuercher jails...")
    jails = update_jails_json()
    
    print("\nUpdating README.md with current jails table...")
    update_readme(jails)
    
    print("\nAll updates complete!")

if __name__ == "__main__":
    main()
