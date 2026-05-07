from anthropic import Anthropic

client = Anthropic(api_key="YOUR_API_KEY")

response = client.messages.create(
    model="claude-3-sonnet-20240229",
    max_tokens=100,
    messages=[{"role": "user", "content": "Say hello"}]
)

print(response.content[0].text)