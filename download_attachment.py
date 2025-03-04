from confluence_sync.api.confluence_client import ConfluenceClient
import os
import requests

# Initialize the client
client = ConfluenceClient()

# Get the attachment info
attachments = client.get_page_attachments('6278610971')
attachment = attachments[0]
download_link = attachment.get('_links', {}).get('download')

# Construct the correct download URL
base_url = client.credentials.get('url') + '/wiki'
download_url = base_url + download_link

# Create the attachments directory
os.makedirs('obsidian-test/Obsidian Test Home/Test/_attachments', exist_ok=True)

# Download the attachment
response = requests.get(
    download_url,
    auth=(client.credentials.get('email'), client.credentials.get('api_token')),
    stream=True
)

if response.status_code == 200:
    file_path = 'obsidian-test/Obsidian Test Home/Test/_attachments/CleanShot 2025-03-02 at 09.46.52@2x-20250302-084655.png'
    with open(file_path, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)
    print(f'Download successful: {file_path}')
else:
    print(f'Error downloading attachment: HTTP {response.status_code}') 