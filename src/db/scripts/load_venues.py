#!/usr/bin/env python3
"""Load venues from venues.json into the database, avoiding duplicates."""

import json
import sys
from pathlib import Path

# Add parent directory to path to import from db
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from db.database import Database


def load_venues(db_path: str | Path | None = None) -> None:
    """Load venues from venues.json into the database.
    
    Venues with duplicate names will be updated with the new location and capacity.
    """
    script_dir = Path(__file__).resolve().parent
    venues_file = script_dir / "venues.json"
    
    if not venues_file.exists():
        print(f"Error: {venues_file} not found", file=sys.stderr)
        sys.exit(1)
    
    with open(venues_file) as f:
        venues_data = json.load(f)
    
    if not isinstance(venues_data, list):
        print("Error: venues.json must contain a JSON array", file=sys.stderr)
        sys.exit(1)
    
    with Database(db_path) if db_path else Database() as db:
        added = 0
        updated = 0
        
        for venue in venues_data:
            name = venue.get("name")
            city = venue.get("city")
            max_capacity = venue.get("max_capacity")
            
            if not name or not city or max_capacity is None:
                print(f"Warning: Skipping invalid venue (missing name, city, or max_capacity): {venue}", file=sys.stderr)
                continue
            
            existing = db.venues.get(name)
            db.venues.add(name, city, max_capacity)
            
            if existing:
                updated += 1
                print(f"Updated: {name} -> {city} (capacity: {max_capacity})")
            else:
                added += 1
                print(f"Added: {name} -> {city} (capacity: {max_capacity})")
        
        print(f"\nSummary: {added} venues added, {updated} venues updated")


if __name__ == "__main__":
    db_path = sys.argv[1] if len(sys.argv) > 1 else None
    load_venues(db_path)
