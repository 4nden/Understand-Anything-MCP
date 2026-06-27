import os
import stripe
from dotenv import load_dotenv

# Load env variables (make sure STRIPE_SECRET_KEY is set in backend/.env)
load_dotenv()
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

def create_checkout_session(tier_name: str):
    try:
        # Create a test product and price on the fly
        product = stripe.Product.create(name=f"Understand-Anything {tier_name} Tier")
        price = stripe.Price.create(
            product=product.id,
            unit_amount=2900 if tier_name == "Pro" else 9900,
            currency="usd",
        )

        # Create the checkout session with the required metadata!
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{"price": price.id, "quantity": 1}],
            mode="payment",
            success_url="https://understand-anything.example.com/success",
            cancel_url="https://understand-anything.example.com/cancel",
            metadata={"tier": tier_name} # <--- THIS IS THE CRITICAL PIECE
        )

        print(f"\n✅ Successfully created {tier_name} Checkout Session!")
        print(f"🔗 Go to this URL to pay with test card (4242 4242...):")
        print(session.url)
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    print("Which tier do you want to test?")
    print("1. Pro")
    print("2. Team")
    choice = input("Enter 1 or 2: ")
    
    if choice == "1":
        create_checkout_session("Pro")
    elif choice == "2":
        create_checkout_session("Team")
    else:
        print("Invalid choice")
