import requests
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential
from azure.ai.projects.models import FunctionTool, ToolSet
from typing import Any, Callable, Set, Dict, List, Optional
from config import API_BASE_URL, API_HEADERS



def list_object_details(headers: Optional[Dict[str, str]] = None) -> str:
    """
    Calls the listObjectDetails API endpoint to get all available objects.

    :param headers (Dict[str, str], optional): Additional headers to include in the request
    :return: Formatted string containing object details
    :rtype: str
    """
    endpoint = f"{API_BASE_URL}/tools/objects/get_name_of_object"
    
    # Use default headers from config
    default_headers = API_HEADERS.copy()
    
    # Merge with provided headers
    if headers:
        default_headers.update(headers)
    
    try:
        response = requests.get(endpoint, headers=default_headers)
        response.raise_for_status()  # Raises an HTTPError for bad responses (4xx, 5xx)
        data = response.json()
        
        # Format the response into a readable string
        if isinstance(data, dict) and 'data' in data:
            objects = data['data']
            if not objects:
                return "No objects found in the system."
            
            result = "Available Objects:\n"
            for obj in objects:
                result += f"\nObject Name: {obj.get('objectName', 'N/A')}\n"
                result += f"Description: {obj.get('objectDescription', 'N/A')}\n"
                result += f"Type: {obj.get('objectType', 'N/A')}\n"
                result += "-" * 50
            return result
        else:
            return f"Unexpected response format: {data}"
            
    except requests.exceptions.RequestException as e:
        return f"Error fetching object details: {str(e)}"

# Statically defined user functions for fast reference
user_functions: Set[Callable[..., Any]] = {
    list_object_details,
}



# Create an Azure AI Client from a connection string, copied from your Azure AI Foundry project.
# It should be in the format "<HostName>;<AzureSubscriptionId>;<ResourceGroup>;<HubName>"
# Customers need to login to Azure subscription via Azure CLI and set the environment variables

project_client = AIProjectClient.from_connection_string(
    credential=DefaultAzureCredential(),
    conn_str="",
)

# Initialize agent toolset with user functions
functions = FunctionTool(user_functions)
toolset = ToolSet()
toolset.add(functions)

agent = project_client.agents.create_agent(
    model="gpt-4o-mini", 
    name="sriram-function-calling-agent", 
    instructions="""You are an AI assistant that helps users retrieve information about available objects from the system.

Your main capability is to list all available objects using the list_object_details API endpoint. This endpoint returns:
- objectName
- objectDescription
- objectType

When users ask about available objects or need to see the list of objects, use the list_object_details function to fetch this information.

The API is already configured with the necessary authentication headers, so you don't need to worry about authentication.

If you encounter any errors while calling the API, return the error message to the user in a clear and helpful way.

Remember to:
1. Use the list_object_details function when users ask about available objects
2. Present the information in a clear, organized manner
3. Handle any errors gracefully and explain them to the user
4. Don't make assumptions about the data - always fetch it fresh from the API""", 
    toolset=toolset
)
print(f"Created agent, ID: {agent.id}")

# Create thread for communication
thread = project_client.agents.create_thread()
print(f"Created thread, ID: {thread.id}")

# Create message to thread
message = project_client.agents.create_message(
    thread_id=thread.id,
    role="user",
    content="Give me the list of objects",
)
print(f"Created message, ID: {message.id}")


# Create and process agent run in thread with tools
run = project_client.agents.create_and_process_run(thread_id=thread.id, agent_id=agent.id)
print(f"Run finished with status: {run.status}")

if run.status == "failed":
    print(f"Run failed: {run.last_error}")


# Fetch and log all messages
messages = project_client.agents.list_messages(thread_id=thread.id)
print(f"Messages: {messages}")