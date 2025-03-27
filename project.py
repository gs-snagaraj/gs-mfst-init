from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient

project_connection_string="<<project_connection_string>>"

project = AIProjectClient.from_connection_string(
  conn_str=project_connection_string,
  credential=DefaultAzureCredential())

chat = project.inference.get_chat_completions_client()
response = chat.complete(
    model="gpt-4o-mini",
    messages=[
        {"role": "system", "content": "You are a helpful writing assistant"},
        {"role": "user", "content": "Write me a poem about flowers"},
    ]
)

print(response.choices[0].message.content)