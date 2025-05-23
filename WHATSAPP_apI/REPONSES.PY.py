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
