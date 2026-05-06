TOOLS = [
    # ── Patient ──────────────────────────────────────────────────────────────
    {
        "type": "function",
        "function": {
            "name": "register_patient",
            "description": (
                "Register a new patient. "
                "IMPORTANT: Always call search_patient first. Only call this if the patient was not found. "
                "Requires name and phone. Ask for them if missing."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Full name of the patient"},
                    "phone": {
                        "type": "string",
                        "description": "10-digit Indian mobile number (with or without +91 prefix)",
                    },
                    "dob": {
                        "type": "string",
                        "description": "Date of birth in YYYY-MM-DD format. Omit if not provided.",
                    },
                    "gender": {
                        "type": "string",
                        "enum": ["male", "female", "other"],
                        "description": "Patient gender. Omit if not provided.",
                    },
                },
                "required": ["name", "phone"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_patient",
            "description": "Fetch a patient's full profile including allergies and history by their numeric ID.",
            "parameters": {
                "type": "object",
                "properties": {
                    "patient_id": {"type": "integer", "description": "Patient's numeric ID"},
                },
                "required": ["patient_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_patient",
            "description": (
                "Search for a patient by name or phone number. "
                "Always call this before register_patient to avoid duplicates. "
                "Returns up to 5 matching patients with their IDs."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Full or partial patient name, or full/partial phone number (min 2 characters)",
                    },
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
            "description": (
                "Book an appointment for a patient. "
                "Requires a valid patient_id (from search or register). "
                "slot_time must be a future date and time. "
                "Default doctor_id is 1 unless another is specified."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "patient_id": {"type": "integer", "description": "Patient's numeric ID"},
                    "doctor_id": {
                        "type": "integer",
                        "description": "Doctor ID. Use 1 if not specified.",
                    },
                    "slot_time": {
                        "type": "string",
                        "description": "Future appointment time in YYYY-MM-DD HH:MM (24-hour) format",
                    },
                },
                "required": ["patient_id", "doctor_id", "slot_time"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_todays_queue",
            "description": "Get today's confirmed appointments for a doctor, ordered by token number.",
            "parameters": {
                "type": "object",
                "properties": {
                    "doctor_id": {
                        "type": "integer",
                        "description": "Doctor ID. Use 1 if not specified.",
                    },
                },
                "required": ["doctor_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_queue_position",
            "description": "Check a patient's current queue position and estimated wait time.",
            "parameters": {
                "type": "object",
                "properties": {
                    "appointment_id": {"type": "integer", "description": "Appointment ID"},
                },
                "required": ["appointment_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "cancel_appointment",
            "description": "Cancel a patient's appointment and free the slot.",
            "parameters": {
                "type": "object",
                "properties": {
                    "appointment_id": {"type": "integer", "description": "Appointment ID to cancel"},
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
            "description": (
                "Open a new clinical visit for a patient. "
                "Must be called before save_emr or draft_prescription. "
                "If a visit is already open for the patient, the existing visit_id is returned."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "patient_id": {"type": "integer", "description": "Patient's numeric ID"},
                },
                "required": ["patient_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "structure_emr",
            "description": (
                "Convert raw doctor notes into structured SOAP format. "
                "Returns soap_notes with subjective, objective, assessment, plan fields. "
                "Always call save_emr immediately after with the returned soap_notes."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "raw_text": {
                        "type": "string",
                        "description": "Raw clinical notes as dictated or typed by the doctor (min 10 characters)",
                    },
                },
                "required": ["raw_text"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "save_emr",
            "description": (
                "Save structured SOAP notes to an open visit. "
                "Use the soap_notes object returned by structure_emr. "
                "Optionally include a diagnosis string."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "visit_id": {"type": "integer", "description": "Visit ID from create_visit"},
                    "soap_notes": {
                        "type": "object",
                        "description": "SOAP notes from structure_emr",
                        "properties": {
                            "subjective": {"type": "string", "description": "Patient complaints and history"},
                            "objective": {"type": "string", "description": "Clinical findings and vitals"},
                            "assessment": {"type": "string", "description": "Diagnosis or working diagnosis"},
                            "plan": {"type": "string", "description": "Treatment plan"},
                        },
                        "required": ["subjective", "objective", "assessment", "plan"],
                    },
                    "diagnosis": {
                        "type": "string",
                        "description": "Primary diagnosis text (optional)",
                    },
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
            "description": (
                "Draft a prescription using AI based on symptoms and diagnosis. "
                "Returns a drug list for doctor review. "
                "Show the drugs to the doctor and ask for confirmation before calling save_prescription."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "symptoms": {
                        "type": "string",
                        "description": "Patient's symptoms, e.g. 'fever for 3 days, cough, runny nose'",
                    },
                    "diagnosis": {
                        "type": "string",
                        "description": "Doctor's diagnosis, e.g. 'Viral upper respiratory infection'",
                    },
                },
                "required": ["symptoms", "diagnosis"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "save_prescription",
            "description": (
                "Save an approved prescription to the database. "
                "Only call after the doctor confirms the drug list. "
                "One prescription per visit is allowed."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "visit_id": {"type": "integer", "description": "Visit ID from create_visit"},
                    "drugs": {
                        "type": "array",
                        "description": "Approved drug list from draft_prescription",
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
                    "instructions": {
                        "type": "string",
                        "description": "General patient instructions, e.g. 'Take after meals. Rest well.'",
                    },
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
            "description": (
                "Send a plain text message to a patient or staff via Telegram. "
                "Use for confirmations, instructions, or any clinic communication."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "chat_id": {
                        "type": "string",
                        "description": "Telegram chat ID of the recipient",
                    },
                    "text": {"type": "string", "description": "Message text (plain text only, max 4096 chars)"},
                },
                "required": ["chat_id", "text"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "send_reminder",
            "description": "Send an appointment reminder to a patient via Telegram with their token and slot time.",
            "parameters": {
                "type": "object",
                "properties": {
                    "appointment_id": {"type": "integer", "description": "Appointment ID"},
                    "chat_id": {"type": "string", "description": "Patient's Telegram chat ID"},
                },
                "required": ["appointment_id", "chat_id"],
            },
        },
    },
]
