from flask import Flask, request
import requests
from insertion_data import *
import logging
import os

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s [%(levelname)s] %(message)s')

app = Flask(__name__)

VERIFY_TOKEN = 'mwi007'
ACCESS_TOKEN = 'EAA7KdM6HllcBO7JRU00XYqxG60rY5O6K3ITa2MiRy8jjM6sSxV2jaFSL8kUJHRVDfSlkRqfhoRij62HKzgWZBgJSwUkXruWqspjc2LW6CCywUS84fmpmjBAyJIDIBL6kSZB3YuebdC7vpi0IUiqRETUtwLr2UZCL8xzZBpNTZCWYlvOdnWT9liBy41juZBHJ9I3fBGPDmsHqeJvnexNIOx78kYWgxJC7rtmx9xzplSWUfzlhAZD'
PHONE_NUMBER_ID = '683800431476069'


# In-memory session tracking
users = {}

def send_whatsapp_message(phone_number, message):
    url = f"https://graph.facebook.com/v18.0/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": phone_number,
        "text": {"body": message}
    }
    response = requests.post(url, headers=headers, json=payload)
    logging.info(f"Sent message to {phone_number}: {response.status_code} {response.text}")

@app.route("/webhook", methods=["GET"])
def verify_webhook():
    if request.args.get("hub.verify_token") == VERIFY_TOKEN:
        return request.args.get("hub.challenge")
    return "Verification token mismatch", 403

@app.route("/webhook", methods=["POST"])
def receive_message():
    data = request.get_json()
    if data.get("object"):
        for entry in data.get("entry", []):
            for change in entry.get("changes", []):
                value = change.get("value", {})
                messages = value.get("messages", [])
                for message in messages:
                    if message.get("type") == "text":
                        phone = message["from"]
                        text = message["text"]["body"].strip()
                        process_message(phone, text)
    return "OK", 200

def process_message(phone, message):
    logging.info(f"Message from {phone}: {message}")
    session = users.get(phone)
    db_user = get_user(phone)

    if not session:
        session = {
            "step": "new_user_check",
            "mobile": db_user["mobile"] if db_user else None,
            "name": db_user["name"] if db_user else None,
            "tasks": get_tasks(phone)
        }
        users[phone] = session

    # Step: Greeting
    if message.lower() in ["hi", "hello"]:
        if session["name"]:
            session["step"] = "menu"
            send_whatsapp_message(phone, f"👋 Welcome back, {session['name']}!\n📋 *Task Menu:*\n1. View Tasks\n2. Add Task\n3. Modify Task Description\n4. Update Task Status")
        else:
            session["step"] = "awaiting_mobile"
            send_whatsapp_message(phone, "👋 Hello! Please enter your mobile number to register:")

    # Step: Mobile input
    elif session["step"] == "awaiting_mobile":
        session["mobile"] = message
        session["step"] = "awaiting_name"
        send_whatsapp_message(phone, "📝 Great! Now, please enter your name:")

    # Step: Name input
    elif session["step"] == "awaiting_name":
        session["name"] = message
        create_user(phone, session["mobile"], session["name"])
        session["step"] = "menu"
        send_whatsapp_message(phone, f"✅ You are now registered, {session['name']}!\n📋 *Task Menu:*\n1. View Tasks\n2. Add Task\n3. Modify Task Description\n4. Update Task Status")

    # Step: Menu options
    elif session["step"] == "menu":
        if message == "1":
            tasks = get_tasks(phone)
            if not tasks:
                send_whatsapp_message(phone, "📋 You have no tasks yet.")
            else:
                task_list = "\n".join([f"{i+1}. {t}" for i, t in enumerate(tasks)])
                send_whatsapp_message(phone, f"📋 Your tasks:\n{task_list}")

        elif message == "2":
            session["step"] = "adding"
            send_whatsapp_message(phone, "✏️ Please type the task to add:")

        elif message == "3":  # Modify Task Description
            tasks = get_tasks(phone)
            if not tasks:
                send_whatsapp_message(phone, "❌ No tasks to modify.")
            else:
                session["step"] = "modifying_select"
                session["tasks"] = tasks
                task_list = "\n".join([f"{i+1}. {t}" for i, t in enumerate(tasks)])
                send_whatsapp_message(phone, f"Which task number would you like to modify?\n{task_list}")

        elif message == "4":
            tasks = get_tasks_update(phone)  # returns list of (task, status)
            if not tasks:
                send_whatsapp_message(phone, "❌ No tasks to update status.")
            else:
                session["step"] = "status_update_select"
                session["tasks"] = tasks
                task_list = "\n".join([
                    f"{i + 1}. {t[0]} - ({t[1] if t[1] else 'Pending'})"
                    for i, t in enumerate(tasks)
                ])
                send_whatsapp_message(phone, f"Which task number's status would you like to update?\n{task_list}")

    # Step: Adding task
    elif session["step"] == "adding":
        add_task(phone, message)
        session["step"] = "menu"
        send_whatsapp_message(phone, f"✅ Task added: {message}\n📋 *Task Menu:*\n1. View Tasks\n2. Add Task\n3. Modify Task Description\n4. Update Task Status")

    # Step: Modifying task - select which task
    elif session["step"] == "modifying_select":
        try:
            index = int(message) - 1
            if 0 <= index < len(session["tasks"]):
                session["modify_index"] = index
                session["step"] = "modifying_task"
                send_whatsapp_message(phone, "✏️ Enter the new description for the selected task:")
            else:
                send_whatsapp_message(phone, "❌ Invalid task number.")
        except ValueError:
            send_whatsapp_message(phone, "❌ Please enter a valid number.")

    # Step: Modifying task - get new description
    elif session["step"] == "modifying_task":
        update_task(phone, session["modify_index"], message)
        session["step"] = "menu"
        send_whatsapp_message(phone,
                              f"✏️ Task description updated.\n🕒 Status set to *Pending* by default.\n📋 ")
        send_whatsapp_message(phone,"Task Menu:*\n1. View Tasks\n2. Add Task\n3. Modify Task Description\n4. Update Task Status")

    # Step: Updating status - select task
    # After user selects task number to update
    elif session["step"] == "status_update_select":
        try:
            index = int(message) - 1
            tasks = session.get("tasks", [])
            if 0 <= index < len(tasks):
                task, current_status = tasks[index]
                session["step"] = "status_update_confirm"
                session["selected_task_index"] = index
                send_whatsapp_message(phone,
                                      f"Current status of '{task}' is '{current_status or 'Pending'}'.\n"
                                      "Reply with:\n1. Done\n2. Pending")
            else:
                send_whatsapp_message(phone, "❌ Invalid task number.")
        except (ValueError, TypeError):
            send_whatsapp_message(phone, "❌ Invalid selection. Please enter a valid number.")

    # After user selects new status
    elif session.get("step") == "status_update_confirm":
        selected_task_index = session.get("selected_task_index")
        tasks = session.get("tasks", [])
        if selected_task_index is None or not tasks:
            send_whatsapp_message(phone, "❌ Session expired or invalid. Please start again.")
            session.clear()
            # users.pop(phone,None)
            return

        if message == "1":
            new_status = "Done"
            send_whatsapp_message(phone, "Task has been Done.")
        elif message == "2":
            new_status = "Pending"
        else:
            send_whatsapp_message(phone, "❌ Invalid option. Please reply with 1 or 2.")
            return

        task_to_update = tasks[selected_task_index][0]

        # Update the status in your database or data store
        update_task_status(phone, task_to_update, new_status)

        send_whatsapp_message(phone, f"✅ Status of task '{task_to_update}' updated to '{new_status}'.")
        session.clear()



    else:
        send_whatsapp_message(phone, "Invalid input. Let's start over.\nPlease type Hi or Hello to begin.")
        session["step"] = "menu"

if __name__ == "__main__":
    from db_setup import init_db
    init_db()
    # app.run(port=5000, debug=True)
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
