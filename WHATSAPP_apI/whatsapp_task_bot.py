from flask import Flask, request
import requests
from insertion_data import *
import logging

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s [%(levelname)s] %(message)s')


app = Flask(__name__)

VERIFY_TOKEN = 'my_verify_token_123'
ACCESS_TOKEN = 'EAA7KdM6HllcBO9bnLfgKXqkN6OnO7X5SNIqmmOpLqVyMFsHrmQIq5fOs9fcHjl5snu6bpNEIhqKrsbtLKBZBTTHfZBZCpyAHjbQFYMRmA3c5BvoTy2BO8WvTxiR44WqsWnHQVVE7eFLwZAXcQT5y6aJbf3FQRtQd2E1BTwDYzKm9MaBjts5jQOZAOa5PLgXjC71sT6ZClB1KYGrXCAMULsK2msoj09c2b7TZCpAMkgZD'
PHONE_NUMBER_ID = '683800431476069'

# In-memory user store
users = {}

# Send WhatsApp message
def send_whatsapp_message(phone_number, message):
    url = f"https://graph.facebook.com/v18.0/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp_bot",
        "to": phone_number,
        "text": {"body": message}
    }
    response = requests.post(url, headers=headers, json=payload)
    print("WA API Response:", response.status_code, response.text)


# GET route for verification
@app.route("/webhook", methods=["GET"])
def verify_webhook():
    if request.args.get("hub.verify_token") == VERIFY_TOKEN:
        return request.args.get("hub.challenge")
    return "Verification token mismatch", 403

# POST route for incoming messages
@app.route("/webhook", methods=["POST"])
def receive_message():
    data = request.get_json()
    if data.get("object"):
        for entry in data.get("entry", []):
            changes = entry.get("changes", [])
            for change in changes:
                value = change.get("value", {})
                messages = value.get("messages", [])
                for message in messages:
                    if message.get("type") == "text" and "text" in message:
                        phone = message["from"]
                        text = message["text"]["body"].strip()
                        process_message(phone, text)
    return "OK", 200

# Main logic handler
def process_message(user, message):
    logging.info(f"User: {user}, Message: {message}")
    session = users.get(user)

    db_user = get_user(user)

    if not session:
        session = {
            "step": "new_user_check",
            "mobile": db_user["mobile"] if db_user else None,
            "name": db_user["name"] if db_user else None,
            "tasks": get_tasks(user),
        }
        users[user] = session

    # The rest of your message handling remains the same, but:
    # - call `create_user()` when registering a new user
    # - call `add_task()` and `update_task()` accordingly


    # Step 1: Detect if "Hi" and new or existing user
    if message.lower() in ["hi", "hello"]:
        if session["name"]:  # existing user
            session["step"] = "menu"
            send_whatsapp_message(user, f"👋 Welcome back, {session['name']}!\n📋 *Task Menu:*\n1. View Tasks\n2. Add Task\n3. Update Task")
        else:
            session["step"] = "awaiting_mobile"
            send_whatsapp_message(user, "👋 Hello! Let's get you registered.\n📱 Please enter your mobile number:")

    elif session["step"] == "awaiting_mobile":
        session["mobile"] = message
        session["step"] = "awaiting_name"
        send_whatsapp_message(user, "👤 Please enter your name:")

    elif session["step"] == "awaiting_name":
        session["name"] = message
        session["step"] = "menu"
        send_whatsapp_message(user, f"✅ Welcome, {session['name']}! You have been registered.\n📋 *Task Menu:*\n1. View Tasks\n2. Add Task\n3. Update Task")

    elif session["step"] == "menu":
        if message == "1":
            if not session["tasks"]:
                send_whatsapp_message(user, "📋 You have no tasks yet.")
            else:
                task_list = "\n".join([f"{i+1}. {task}" for i, task in enumerate(session["tasks"])])
                send_whatsapp_message(user, f"📋 Your tasks:\n{task_list}")
        elif message == "2":
            session["step"] = "adding"
            send_whatsapp_message(user, "✏️ Please enter the task you want to add:")
        elif message == "3":
            if not session["tasks"]:
                send_whatsapp_message(user, "❌ No tasks to update.")
            else:
                session["step"] = "updating_select"
                task_list = "\n".join([f"{i+1}. {task}" for i, task in enumerate(session["tasks"])])
                send_whatsapp_message(user, f"Which task number do you want to update?\n{task_list}")
        else:
            send_whatsapp_message(user, "📋 *Task Menu:*\n1. View Tasks\n2. Add Task\n3. Update Task")

    elif session["step"] == "adding":
        session["tasks"].append(message)
        session["step"] = "menu"
        send_whatsapp_message(user, f"✅ Task added: {message}\n\n📋 *Task Menu:*\n1. View Tasks\n2. Add Task\n3. Update Task")

    elif session["step"] == "updating_select":
        try:
            task_index = int(message) - 1
            if 0 <= task_index < len(session["tasks"]):
                session["update_index"] = task_index
                session["step"] = "updating_task"
                send_whatsapp_message(user, "✏️ Enter the new task description:")
            else:
                send_whatsapp_message(user, "❌ Invalid task number. Try again.")
        except ValueError:
            send_whatsapp_message(user, "❌ Please enter a valid number.")

    elif session["step"] == "updating_task":
        idx = session["update_index"]
        session["tasks"][idx] = message
        session["step"] = "menu"
        send_whatsapp_message(user, f"✅ Task updated.\n\n📋 *Task Menu:*\n1. View Tasks\n2. Add Task\n3. Update Task")

if __name__ == "__main__":
    app.run(port=5000, debug=True)

