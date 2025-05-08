from db.payments import get_payment_score

score = get_payment_score(1)
print(f"Payment Score for User 1: {score}")
