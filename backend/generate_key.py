import argparse
from models import SessionLocal, LicenseKey
import secrets

def generate_secure_key():
    return "UA-" + secrets.token_urlsafe(16)

def main():
    parser = argparse.ArgumentParser(description="Generate a license key")
    parser.add_argument("--tier", default="Pro", choices=["Free", "Pro", "Team"], help="License tier")
    parser.add_argument("--email", default="", help="Customer email")
    args = parser.parse_args()

    db = SessionLocal()
    new_key = generate_secure_key()
    
    db_key = LicenseKey(key=new_key, tier=args.tier, email=args.email)
    db.add(db_key)
    db.commit()
    db.refresh(db_key)
    
    print(f"Success! Generated new key:")
    print(f"Key: {new_key}")
    print(f"Tier: {args.tier}")
    print(f"Email: {args.email}")
    db.close()

if __name__ == "__main__":
    main()
