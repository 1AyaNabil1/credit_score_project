from logic.calculator import calculate_iScore
from db.users import get_all_users

for user in get_all_users():
    score = calculate_iScore(user["user_id"])
    print(f"User: {user['full_name']}, iScore: {score}")
