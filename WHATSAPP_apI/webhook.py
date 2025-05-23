from flask import Flask, request
import requests

app = Flask(__name__)

# Store users and their session data
users = {}

# Constants
PHONE_NUMBER_ID = '683800431476069'
VERIFY_TOKEN = 'my_verify_token_123'
ACCESS_TOKEN = 'EAA7KdM6HllcBO9bnLfgKXqkN6OnO7X5SNIqmmOpLqVyMFsHrmQIq5fOs9fcHjl5snu6bpNEIhqKrsbtLKBZBTTHfZBZCpyAHjbQFYMRmA3c5BvoTy2BO8WvTxiR44WqsWnHQVVE7eFLwZAXcQT5y6aJbf3FQRtQd2E1BTwDYzKm9MaBjts5jQOZAOa5PLgXjC71sT6ZClB1KYGrXCAMULsK2msoj09c2b7TZCpAMkgZD'
META_URL = f"https://graph.facebook.com/v18.0/{PHONE_NUMBER_ID}/messages"

# Send WhatsApp message function
def send_whatsapp_message(user, message):
    payload = {
        "messaging_product": "whatsapp_bot",
        "to": user,
        "type": "text",
        "text": {
            "body": message
        }
    }
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    requests.post(META_URL, json=payload, headers=headers)

# Send interactive menu for WhatsApp
def send_whatsapp_interactive_menu(user):
    payload = {
        "messaging_product": "whatsapp_bot",
        "to": user,
        "type": "interactive",
        "interactive": {
            "type": "button",
            "header": {
                "type": "text",
                "text": "Task"
            },
            "body": {
                "text": "Welcome to To Do Task"
            },
            "action": {
                "buttons": [
                    {
                        "type": "reply",
                        "reply": {
                            "id": "view_tasks",
                            "title": "📋 View My Task"
                        }
                    },
                    {
                        "type": "reply",
                        "reply": {
                            "id": "add_task",
                            "title": "➕ Add A New Task"
                        }
                    },
                    {
                        "type": "reply",
                        "reply": {
                            "id": "mark_done",
                            "title": "✔️ Mark Task as Done"
                        }
                    }
                ]
            }
        }
    }
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    requests.post(META_URL, json=payload, headers=headers)

# Webhook for receiving WhatsApp messages
@app.route('/webhook', methods=['GET', 'POST'])
def webhook():
    data = request.get_json()
    try:
        entry = data.get('entry', [])[0]
        changes = entry.get('changes', [])[0]
        value = changes.get('value', {})
        messages = value.get('messages', [])

        if messages:
            message = messages[0]
            user = message.get('from')
            message_type = message.get('type')

            if message_type == "text":
                text = message['text']['body'].strip()
                process_message(user, text)


            elif message_type == "button":
                button_payload = message['button'].get('payload') or message['button'].get('text')
                process_message(user, button_payload)

        else:
            print("No messages found in webhook")

    except Exception as e:
        print("Webhook error:", e)

    return "OK", 200

# Process the incoming message
def process_message(user, message):
    if user not in users:
        users[user] = {
            "step": "new_user_check",
            "mobile": None,
            "name": None,
            "tasks": []
        }

    session = users[user]
    message = message.lower().strip()

    # Initial greeting
    if message in ["hi", "hello"]:
        if session["name"]:
            session["step"] = "menu"
            send_whatsapp_interactive_menu(user)
        else:
            session["step"] = "awaiting_mobile"
            send_whatsapp_message(user, "👋 Hello! Let's get you registered.\n📱 Please enter your mobile number:")

    # Awaiting mobile input
    elif session["step"] == "awaiting_mobile":
        session["mobile"] = message
        session["step"] = "awaiting_name"
        send_whatsapp_message(user, "👤 Please enter your name:")

    # Awaiting name input
    elif session["step"] == "awaiting_name":
        session["name"] = message
        session["step"] = "menu"
        send_whatsapp_interactive_menu(user)

    # View tasks
    elif message == "view_tasks":
        if not session["tasks"]:
            send_whatsapp_message(user, "📋 You have no tasks yet.")
        else:
            task_list = "\n".join([f"{i+1}. {task['title']} - *{task['status']}*" for i, task in enumerate(session["tasks"])])
            send_whatsapp_message(user, f"📋 Your tasks:\n{task_list}")

    # Add a new task
    elif message == "add_task":
        session["step"] = "adding"
        send_whatsapp_message(user, "✏️ Please enter the task you want to add:")

    # Task details entry
    elif session["step"] == "adding":
        session["new_task_title"] = message
        session["step"] = "adding_status"
        send_whatsapp_message(user, "🔘 What is the status of this task?\nReply with:\n1. Pending\n2. In Progress\n3. Completed")

    # Task status selection
    elif session["step"] == "adding_status":
        status_map = {
            "1": "Pending",
            "2": "In Progress",
            "3": "Completed"
        }
        status = status_map.get(message)
        if status:
            session["tasks"].append({
                "title": session["new_task_title"],
                "status": status
            })
            del session["new_task_title"]
            session["step"] = "menu"
            send_whatsapp_message(user, "✅ Task added successfully.")
            send_whatsapp_interactive_menu(user)
        else:
            send_whatsapp_message(user, "❌ Please enter a valid number (1, 2, or 3).")

    # Mark task as done
    elif message == "mark_done":
        if not session["tasks"]:
            send_whatsapp_message(user, "❌ No tasks to mark.")
        else:
            session["step"] = "marking"
            task_list = "\n".join([f"{i+1}. {task['title']} - *{task['status']}*" for i, task in enumerate(session["tasks"])])
            send_whatsapp_message(user, f"✅ Which task number do you want to update status for?\n{task_list}")

    # Mark task status change
    elif session["step"] == "marking":
        try:
            idx = int(message) - 1
            if 0 <= idx < len(session["tasks"]):
                session["marking_task_index"] = idx
                session["step"] = "updating_status"
                send_whatsapp_message(user, "🔁 Choose new status:\n1. Pending\n2. In Progress\n3. Completed")
            else:
                send_whatsapp_message(user, "❌ Invalid task number.")
        except:
            send_whatsapp_message(user, "❌ Please enter a valid number.")

    # Update task status
    elif session["step"] == "updating_status":
        status_map = {
            "1": "Pending",
            "2": "In Progress",
            "3": "Completed"
        }
        new_status = status_map.get(message)
        if new_status:
            idx = session.get("marking_task_index")
            session["tasks"][idx]["status"] = new_status
            del session["marking_task_index"]
            session["step"] = "menu"
            send_whatsapp_message(user, f"✅ Task status updated to *{new_status}*.")
            send_whatsapp_interactive_menu(user)
        else:
            send_whatsapp_message(user, "❌ Invalid choice. Reply with 1, 2, or 3.")

    # Default response
    else:
        send_whatsapp_message(user, "❓ I didn't understand that. Please choose an option from the menu.")
        send_whatsapp_interactive_menu(user)

if __name__ == "__main__":
    app.run(port=5000, debug=True)
