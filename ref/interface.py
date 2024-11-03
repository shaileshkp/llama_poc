from huggingface_hub import InferenceClient

client = InferenceClient(api_key="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")

for message in client.chat_completion(
    model="meta-llama/Llama-3.2-3B-Instruct",
    messages=[{"role": "user", "content": "Given json schema: {\"type\": \"object\", \"properties\": {\"name\": {\"type\": \"string\"}, \"age\": {\"type\": \"number\"}, \"city\": {\"type\": \"string\"}}}, generate questions for collecting data"}], 
    max_tokens=500,
    stream=True,
):
    print(message.choices[0].delta.content, end="")