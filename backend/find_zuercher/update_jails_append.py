#!/usr/bin/env python3
import json
import os
import datetime
import re

# Get the script directory
script_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(script_dir)

# Define file paths
zuercher_jails_file = os.path.join(script_dir, 'zuercher_jails_latest.json')
jails_json_file = os.path.join(root_dir, 'jails.json')
readme_file = os.path.join(root_dir, 'README.md')

# State code to full name mapping
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


def update_jails_json():
    """Update jails.json with new Zuercher jails without replacing existing entries"""
    # Load data
    with open(zuercher_jails_file, 'r', encoding='utf-8') as f:
        zuercher_jails = json.load(f)
    
    with open(jails_json_file, 'r', encoding='utf-8') as f:
        existing_jails = json.load(f)
    
    # Get existing jail IDs
    existing_jail_ids = set(jail.get('jail_id', '') for jail in existing_jails if 'jail_id' in jail)
    
    # Find the highest existing ID
    max_id = 0
    for jail in existing_jails:
        if 'id' in jail and isinstance(jail['id'], int):
            max_id = max(max_id, jail['id'])
    
    # Add new jails
    added_count = 0
    today = datetime.datetime.now().strftime('%Y-%m-%d')
    
    for zuercher_jail in zuercher_jails:
        jail_id = zuercher_jail['jail_id']
        
        # Skip if this jail ID is already in the existing jails
        if jail_id in existing_jail_ids:
            continue
        
        max_id += 1
        new_jail = {
            'id': max_id,
            'jail_name': zuercher_jail['jail_name'],
            'state': zuercher_jail['state'],
            'jail_id': jail_id,  # Keep original jail_id format
            'scrape_system': zuercher_jail['scrape_system'],
            'active': True,
            'created_date': today,
            'updated_date': today,
            'last_scrape_date': None
        }
        existing_jails.append(new_jail)
        existing_jail_ids.add(jail_id)  # Add to set to prevent duplicates
        added_count += 1
    
    # Save updated jails
    if added_count > 0:
        with open(jails_json_file, 'w', encoding='utf-8') as f:
            json.dump(existing_jails, f, indent=4)
        print(f"Added {added_count} new jails to jails.json")
    else:
        print("No new jails to add to jails.json")
    
    return added_count


def update_readme():
    """Update README.md with new Zuercher jails without replacing existing entries"""
    # Load Zuercher jails data
    with open(zuercher_jails_file, 'r', encoding='utf-8') as f:
        zuercher_jails = json.load(f)
    
    # Read current README.md
    with open(readme_file, 'r', encoding='utf-8') as f:
        readme_content = f.read()
    
    # Find the table section
    table_pattern = r'\| State\s+\| Jail\s+\| Jail ID\s+\| Added In Version\s+\| Mugshot\s+\|(.*?)(?=\n\n)'
    table_match = re.search(table_pattern, readme_content, re.DOTALL)
    
    if not table_match:
        print("Could not find the jails table in README.md")
        return 0
    
    # Extract the current table rows
    table_rows = table_match.group(1).strip().split('\n')
    
    # Parse existing jail entries
    existing_jails = set()
    for row in table_rows:
        if '|' in row and not row.startswith('|---'):
            parts = [part.strip() for part in row.split('|')]
            if len(parts) >= 5:  # Valid row
                state = parts[1]
                county = parts[2]
                jail_id = parts[3]
                
                # Create a unique key for each jail
                jail_key = f"{state}:{county}:{jail_id}"
                existing_jails.add(jail_key)
    
    # Prepare new jails for the table
    new_jails = []
    for jail in zuercher_jails:
        state_code = jail['state']
        state_name = state_names.get(state_code, state_code)
        
        # Extract county name
        county = jail['county']
        if "Parish" in county:
            county = county.replace(" Parish", "")
        county_display = f"{county} County"
        
        # Use the exact jail_id from the Zuercher data
        jail_id = jail['jail_id']
        
        # Create a unique key for this jail
        jail_key = f"{state_name}:{county_display}:{jail_id}"
        
        # Add only if not already in the README
        if jail_key not in existing_jails:
            new_jails.append({
                'state': state_name,
                'county': county_display,
                'jail_id': jail_id,
                'version': '3.0.0',
                'mugshot': ':white_check_mark:'
            })
            existing_jails.add(jail_key)  # Mark as processed
    
    # If no new jails to add, exit
    if not new_jails:
        print("No new jails to add to README.md")
        return 0
    
    # Sort new jails by state and county
    new_jails.sort(key=lambda j: (j['state'], j['county']))
    
    # Format new rows for the table
    new_rows = []
    for jail in new_jails:
        state_text = jail['state'].ljust(8)
        county_text = jail['county'].ljust(15)
        jail_id_text = jail['jail_id'].ljust(15)
        version_text = jail['version'].ljust(16)
        mugshot_text = jail['mugshot']
        
        new_rows.append(f"| {state_text} | {county_text} | {jail_id_text} | {version_text} | {mugshot_text} |")
    
    # Get the table header and separators
    table_header = "| State    | Jail              | Jail ID          | Added In Version | Mugshot                     |"
    table_separator = "|----------|-------------------|------------------|------------------|-----------------------------|"
    
    # Extract content before and after the table
    pre_table = readme_content.split(table_header)[0]
    post_table = readme_content.split(table_match.group(0))[-1]
    
    # Reconstruct the README
    updated_readme = pre_table + table_header + "\n" + table_separator + "\n" + "\n".join(table_rows) + "\n" + "\n".join(new_rows) + post_table
    
    # Write the updated README
    with open(readme_file, 'w', encoding='utf-8') as f:
        f.write(updated_readme)
    
    print(f"Added {len(new_jails)} new jails to README.md")
    return len(new_jails)


def main():
    """Main function to update jails.json and README.md"""
    print("Starting update process...")
    
    # First update jails.json
    jails_added = update_jails_json()
    
    # Then update README.md
    readme_added = update_readme()
    
    print(f"\nSummary:\n- Added {jails_added} new jails to jails.json\n- Added {readme_added} new jails to README.md")
    print("Update process complete!")


if __name__ == "__main__":
    main()
