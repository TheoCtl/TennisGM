#!/usr/bin/env python3
"""
Utility script to initialize World Crown tournament data for existing save files.
This adds the World Crown system to saves that were created before this feature existed.
"""

import json
import os
import sys

def initialize_world_crown_data(save_path):
    """Add World Crown data structure to an existing save file"""
    
    # Check if file exists
    if not os.path.exists(save_path):
        print(f"Error: Save file {save_path} not found!")
        return False
    
    try:
        # Load existing save data
        with open(save_path, 'r', encoding='utf-8') as f:
            save_data = json.load(f)
        
        # Check if World Crown data already exists
        if 'world_crown' in save_data:
            print(f"World Crown data already exists in {save_path}")
            return True
        
        # Add World Crown data structure
        save_data['world_crown'] = {
            'current_bracket': {},
            'current_year_teams': {},
            'match_results': {},
            'winners_history': [],
            'pending_matches': []
        }
        
        # Create backup of original file
        backup_path = save_path + '.backup'
        with open(backup_path, 'w', encoding='utf-8') as f:
            json.dump(json.load(open(save_path, 'r', encoding='utf-8')), f, indent=2)
        
        print(f"Created backup: {backup_path}")
        
        # Save updated data
        with open(save_path, 'w', encoding='utf-8') as f:
            json.dump(save_data, f, indent=2)
        
        print(f"Successfully added World Crown data to {save_path}")
        return True
        
    except Exception as e:
        print(f"Error processing {save_path}: {str(e)}")
        return False

def main():
    # Default paths to check
    save_paths = [
        'data/save.json',
        '../data/save.json'
    ]
    
    # Check for command line argument
    if len(sys.argv) > 1:
        save_paths = [sys.argv[1]]
    
    print("World Crown Tournament Initializer")
    print("=" * 40)
    
    success_count = 0
    total_count = 0
    
    for save_path in save_paths:
        if os.path.exists(save_path):
            print(f"\nProcessing: {save_path}")
            total_count += 1
            
            if initialize_world_crown_data(save_path):
                success_count += 1
        else:
            print(f"Save file not found: {save_path}")
    
    print(f"\n" + "=" * 40)
    print(f"Processed {success_count}/{total_count} save files successfully")
    
    if total_count == 0:
        print("\nNo save files found in default locations:")
        for path in ['data/save.json', '../data/save.json']:
            print(f"  - {path}")
        print("\nUsage: python initialize_world_crown.py [save_file_path]")

if __name__ == "__main__":
    main()
