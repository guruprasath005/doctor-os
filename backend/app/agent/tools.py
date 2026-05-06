TOOLS = [
    # ── Patient ──────────────────────────────────────────────────────────────
    {
        "type": "function",
        "function": {
            "name": "register_patient",
            "description": "Register a new patient. Use when a patient has never visited the clinic before.",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Full name of the patient"},
                    "phone": {"type": "string", "description": "Patient's mobile number"},
                    "dob": {"type": "string", "description": "Date of birth in YYYY-MM-DD format"},
                    "gender": {"type": "string", "enum": ["male", "female", "other"]},
                },
                "required": ["name", "phone"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_patient",
            "description": "Fetch a patient's full profile by their ID.",
            "parameters": {
                "type": "object",
                "properties": {
                    "patient_id": {"type": "integer", "description": "Patient ID"},
                },
                "required": ["patient_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_patient",
            "description": "Search for a patient by name or phone number. Use before registering to check if they already exist.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Name or phone number to search"},
                },
                "required": ["query"],
            },
        },
    },
    # ── Appointment ───────────────────────────────────────────────────────────
    {
        "type": "function",
        "function": {
            "name": "create_appointment",
            "description": "Book an appointment for a patient with a doctor.",
            "parameters": {
                "type": "object",
                "properties": {
                    "patient_id": {"type": "integer"},
                    "doctor_id": {"type": "integer", "description": "Doctor ID. Use 1 if not specified."},
                    "slot_time": {"type": "string", "description": "Appointment slot in YYYY-MM-DD HH:MM format"},
                },
                "required": ["patient_id", "doctor_id", "slot_time"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_todays_queue",
            "description": "Get the full list of today's patients for a doctor.",
            "parameters": {
                "type": "object",
                "properties": {
                    "doctor_id": {"type": "integer", "description": "Doctor ID. Use 1 if not specified."},
                },
                "required": ["doctor_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_queue_position",
            "description": "Get a patient's current queue position and estimated wait time.",
            "parameters": {
                "type": "object",
                "properties": {
                    "appointment_id": {"type": "integer"},
                },
                "required": ["appointment_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "cancel_appointment",
            "description": "Cancel a patient's appointment.",
            "parameters": {
                "type": "object",
                "properties": {
                    "appointment_id": {"type": "integer"},
                },
                "required": ["appointment_id"],
            },
        },
    },
    # ── EMR ───────────────────────────────────────────────────────────────────
    {
        "type": "function",
        "function": {
            "name": "create_visit",
            "description": "Open a new visit record for a patient before recording clinical findings.",
            "parameters": {
                "type": "object",
                "properties": {
                    "patient_id": {"type": "integer"},
                },
                "required": ["patient_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "structure_emr",
            "description": "Convert raw doctor notes into structured SOAP format.",
            "parameters": {
                "type": "object",
                "properties": {
                    "raw_text": {"type": "string", "description": "Raw unstructured clinical notes"},
                },
                "required": ["raw_text"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "save_emr",
            "description": "Save structured SOAP notes to a visit.",
            "parameters": {
                "type": "object",
                "properties": {
                    "visit_id": {"type": "integer"},
                    "soap_notes": {
                        "type": "object",
                        "properties": {
                            "subjective": {"type": "string"},
                            "objective": {"type": "string"},
                            "assessment": {"type": "string"},
                            "plan": {"type": "string"},
                        },
                        "required": ["subjective", "objective", "assessment", "plan"],
                    },
                    "diagnosis": {"type": "string"},
                },
                "required": ["visit_id", "soap_notes"],
            },
        },
    },
    # ── Prescription ──────────────────────────────────────────────────────────
    {
        "type": "function",
        "function": {
            "name": "draft_prescription",
            "description": "Draft a prescription based on symptoms and diagnosis.",
            "parameters": {
                "type": "object",
                "properties": {
                    "symptoms": {"type": "string"},
                    "diagnosis": {"type": "string"},
                },
                "required": ["symptoms", "diagnosis"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "save_prescription",
            "description": "Save an approved prescription to the database.",
            "parameters": {
                "type": "object",
                "properties": {
                    "visit_id": {"type": "integer"},
                    "drugs": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string"},
                                "dosage": {"type": "string"},
                                "frequency": {"type": "string"},
                                "duration": {"type": "string"},
                                "instructions": {"type": "string"},
                            },
                            "required": ["name", "dosage", "frequency", "duration"],
                        },
                    },
                    "instructions": {"type": "string"},
                },
                "required": ["visit_id", "drugs"],
            },
        },
    },
    # ── Messaging ─────────────────────────────────────────────────────────────
    {
        "type": "function",
        "function": {
            "name": "send_message",
            "description": "Send a Telegram message to a patient or doctor by their chat ID.",
            "parameters": {
                "type": "object",
                "properties": {
                    "chat_id": {"type": "string", "description": "Telegram chat ID of the recipient"},
                    "text": {"type": "string", "description": "Message text to send"},
                },
                "required": ["chat_id", "text"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "send_reminder",
            "description": "Send an appointment reminder to the patient via Telegram.",
            "parameters": {
                "type": "object",
                "properties": {
                    "appointment_id": {"type": "integer"},
                    "chat_id": {"type": "string", "description": "Patient's Telegram chat ID"},
                },
                "required": ["appointment_id", "chat_id"],
            },
        },
    },
]
