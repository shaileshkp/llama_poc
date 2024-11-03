from huggingface_hub import InferenceClient
import json 

client = InferenceClient(api_key="xxxxx")

# Example schema and JSON data to validate
json_schema = {
    "type": "object",
    "properties": {
        "name": {"type": "string", "description": "The full name of the user"},
        "age": {"type": "number", "description": "The age of the user"},
        "city": {"type": "string", "description": "The city where the user resides"},
        "state": {"type": "string", "description": "The state where the user resides"},
        "country": {"type": "string", "description": "The country where the user resides"},
        "zip_code": {"type": "string", "description": "The ZIP code of the user's location"},
        "contacts": {
            "type": "array",
            "description": "List of contacts for the user",
            "items": {
                "type": "object",
                "properties": {
                    "type": {"type": "string", "description": "Type of contact (e.g., 'email', 'phone')"},
                    "value": {"type": "string", "description": "The contact information"}
                },
                "required": ["type", "value"]
            }
        }
    },
    "required": ["name", "age", "city", "state", "country", "zip_code", "contacts"]
}

# Prepare an empty dictionary to store responses
user_responses = {}

# Function to handle user input with type validation and error handling
def get_valid_input(prompt, expected_type):
    while True:
        user_input = input(prompt)
        try:
            if expected_type == "number":
                return float(user_input)
            elif expected_type == "boolean":
                if user_input.lower() in ["true", "yes", "1"]:
                    return True
                elif user_input.lower() in ["false", "no", "0"]:
                    return False
                else:
                    raise ValueError("Please enter 'yes' or 'no'.")
            elif expected_type == "string":
                return user_input
        except ValueError as e:
            print(f"Invalid input: {e}. Please try again.")

# Function to validate JSON with the LLM and get concise feedback
def validate_json_with_llm(schema, json_data):
    messages = [
        {
            "role": "user",
            "content": (
                f"Given the JSON schema and JSON data below, validate each field concisely. "
                f"Highlight only the errors with a suggestion for correction in a user-friendly way.\n\n"
                f"Schema:\n{json.dumps(schema, indent=2)}\n\n"
                f"JSON data:\n{json.dumps(json_data, indent=2)}\n\n"
                f"Please provide suggestions only for incorrect values."
            )
        }
    ]
    
    # Query the LLM to validate the JSON
    response = client.chat_completion(
        model="microsoft/Phi-3-mini-4k-instruct",
        messages=messages,
        max_tokens=300
    )
    
    # Extract and format the response
    errors = response.choices[0].message.content.strip()
    return errors

# Function to process each field in the schema with validation
def process_schema(schema, responses):
    if schema["type"] == "object":
        for key, value in schema["properties"].items():
            if value["type"] == "array":
                responses[key] = []
                print(f"\n-- Enter details for each item in {key} --")
                while True:
                    item_response = {}
                    process_schema(value["items"], item_response)
                    responses[key].append(item_response)
                    more = input("Add another item? (yes/no): ").strip().lower()
                    if more != "yes":
                        break
            else:
                # Basic type input with validation
                prompt = f"{value.get('description', f'Please enter {key}')}: "
                responses[key] = get_valid_input(prompt, value["type"])

# Main loop to validate and update JSON until the user is satisfied
while True:
    print("\n-- Enter User Information --")
    process_schema(json_schema, user_responses)

    # Validate JSON data with the LLM and get concise suggestions
    errors = validate_json_with_llm(json_schema, user_responses)
    print("\nValidation Results:")
    print(errors)
    
    # Check if there are any issues that require correction
    if "no errors" in errors.lower() or "all valid" in errors.lower():
        print("\nAll fields are valid. Proceeding with final JSON data.")
        break
    
    # Ask user if they want to update any values based on errors
    update_prompt = input("\nDo you want to update any values based on the above errors? (yes/no): ").strip().lower()
    if update_prompt != "yes":
        print("\nFinal JSON Data:")
        print(json.dumps(user_responses, indent=2))
        break
    
    # Process updates based on the errors received
    for error in errors.splitlines():
        if ":" in error:
            field, suggestion = error.split(":", 1)
            field = field.strip()
            suggestion = suggestion.strip()
            print(f"\nCorrection needed for '{field}': {suggestion}")
            prompt = f"Please enter a new value for '{field}': "
            
            # Update only the field with errors
            user_responses[field] = get_valid_input(prompt, json_schema["properties"][field]["type"])

print("\nUser has confirmed the JSON data as correct.")
print(json.dumps(user_responses, indent=2))