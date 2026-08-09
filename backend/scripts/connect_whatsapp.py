"""Connect WhatsApp integration to an organization (CLI helper)."""
import argparse
import os
import sys

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

# Add the parent directory to Python path if running directly
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.config import settings
from app.services.integration_service import save_credentials


def main():
    parser = argparse.ArgumentParser(description="Connect WhatsApp integration for an organization.")
    parser.add_argument("--org-id", required=True, help="Organization ID (UUID)")
    parser.add_argument("--phone-number-id", required=True, help="WhatsApp Phone Number ID")
    parser.add_argument("--access-token", required=True, help="WhatsApp API/Meta Access Token")

    args = parser.parse_args()

    engine = create_engine(settings.DATABASE_URL)
    with Session(engine) as db:
        try:
            # save_credentials(db, organization_id, provider, tokens, metadata)
            row = save_credentials(
                db=db,
                organization_id=args.org_id,
                provider="whatsapp",
                tokens={"access_token": args.access_token},
                metadata={"phone_number_id": args.phone_number_id},
            )
            print(f"SUCCESS: WhatsApp integration connected for organization {args.org_id}")
            print(f"Integration Row ID: {row.id}")
            print(f"Connected: {row.connected}")
            print(f"Phone Number ID: {row.metadata_json.get('phone_number_id')}")
        except Exception as e:
            print(f"ERROR: Failed to connect WhatsApp: {e}")
            sys.exit(1)


if __name__ == "__main__":
    main()
