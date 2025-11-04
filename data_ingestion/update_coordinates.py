import sys
import os

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data_ingestion.data_processor import DataProcessor
from database.db_manager import DatabaseManager


def update_sites_with_coordinates():
    """Update existing sites with latitude and longitude coordinates"""
    print("=== Updating Sites with Coordinates ===")

    # Initialize database manager and data processor
    db_manager = DatabaseManager("clinical_trials.db")
    if not db_manager.connect():
        print("Failed to connect to database")
        return

    data_processor = DataProcessor(db_manager)

    try:
        # Get all sites that don't have coordinates
        query = """
            SELECT site_id, site_name, city, state, country 
            FROM sites_master 
            WHERE latitude IS NULL OR longitude IS NULL
        """
        sites = db_manager.query(query)

        print(f"Found {len(sites)} sites without coordinates")

        updated_count = 0
        for site in sites:
            site_id = site["site_id"]
            site_name = site["site_name"]
            city = site["city"] or ""
            state = site["state"] or ""
            country = site["country"] or ""

            print(f"\nProcessing site: {site_name}")
            print(f"  Location: {city}, {state}, {country}")

            # Geocode the address
            coordinates = data_processor.geocode_address(city, state, country)

            if coordinates:
                # Update the site with coordinates
                update_query = """
                    UPDATE sites_master 
                    SET latitude = ?, longitude = ?
                    WHERE site_id = ?
                """
                success = db_manager.execute(
                    update_query, (coordinates["lat"], coordinates["lon"], site_id)
                )

                if success:
                    print(
                        f"  ✅ Updated coordinates: {coordinates['lat']}, {coordinates['lon']}"
                    )
                    updated_count += 1
                else:
                    print("  ❌ Failed to update coordinates in database")
            else:
                print("  ❌ Failed to geocode address")

        print(f"\n=== Update Summary ===")
        print(f"Successfully updated {updated_count} sites with coordinates")

    except Exception as e:
        print(f"Error updating sites: {e}")
    finally:
        db_manager.disconnect()


if __name__ == "__main__":
    update_sites_with_coordinates()
