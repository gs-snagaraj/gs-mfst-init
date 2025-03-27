import requests
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential
from azure.ai.projects.models import FunctionTool, ToolSet
from typing import Any, Callable, Set, Dict, List, Optional
from config import API_BASE_URL, API_HEADERS



def search_objects(search_key: str, object_type: str) -> str:
    """
    Search for objects by keyword and object type.
    
    Args:
        search_key (str): Search keywords
        object_type (str): Type of object to search for
        
    Returns:
        str: Formatted string containing search results
    """
    endpoint = f"{API_BASE_URL}/tools/objects/search_object"
    
    params = {
        "searchKey": search_key,
        "objectType": object_type
    }
    
    try:
        response = requests.get(
            endpoint,
            headers=API_HEADERS,
            params=params
        )
        response.raise_for_status()  # Raises an HTTPError for bad responses (4xx, 5xx)
        data = response.json()
        
        # Format the response into a readable string
        if isinstance(data, dict) and 'data' in data:
            objects = data['data']
            if not objects:
                return f"No objects found matching search key '{search_key}' and type '{object_type}'."
            
            result = f"Search Results for '{search_key}' (Type: {object_type}):\n"
            for obj in objects:
                result += f"\nObject Metadata: {obj}\n"
                result += "-" * 50
            return result
        else:
            return f"Unexpected response format: {data}"
            
    except requests.exceptions.RequestException as e:
        return f"Error searching objects: {str(e)}"

# Statically defined user functions for fast reference
user_functions: Set[Callable[..., Any]] = {
    search_objects,
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
    name="sriram-function-calling-agent-with-parameters", 
    instructions="""You are an AI assistant that helps users search for objects using the search_objects API.

The search_objects function allows you to search for objects by keyword and object type. Here's how to use it:

1. Function Parameters:
   - search_key (str): The search keywords to find relevant objects
   - object_type (str): The type of object to search for (e.g., "DOCUMENT", "FOLDER", etc.)

2. Function Returns:
   - A string containing formatted search results

3. Response Formatting Guidelines:
   - Start with a clear introduction of the search results
   - List each object in a numbered format
   - For each object, include:
     - Object Name (in bold)
     - Object Label (if available)
     - Object Type (in bold)
     - Description (if available)
   - Use markdown formatting for better readability
   - Add a concluding statement offering further assistance

4. Example Format:
   Here are the search results for objects related to "[search_key]" of type [object_type]:
   
   1. **Object Name:** [name]
      - **Object Label:** [label]
      - **Object Type:** [type]
      - **Description:** [description]
   
   2. **Object Name:** [name]
      ...

5. Error Handling:
   - If no objects are found, clearly state that
   - If there's an error, explain it in a user-friendly way
   - Always maintain a helpful and professional tone

When users ask for object searches:
1. Extract the search key and object type from their query
2. Use the search_objects function with these parameters
3. Format the results according to the guidelines above
4. Present the information in a clear, organized manner
5. Offer to provide more details about specific objects if needed""", 
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
    content="SearchKey is company and objectType is STANDARD",
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

