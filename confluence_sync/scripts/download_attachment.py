"""
Utility script for downloading attachments from Confluence.

This script demonstrates how to download attachments from a Confluence page.
It can be used as a standalone script or imported as a module.
"""

from confluence_sync.api.confluence_client import ConfluenceClient
import os
import requests
import argparse


def download_attachment(page_id, output_dir=None, attachment_index=0):
    """
    Download an attachment from a Confluence page.
    
    Args:
        page_id (str): The ID of the Confluence page.
        output_dir (str, optional): The directory to save the attachment to.
                                   If None, saves to current directory.
        attachment_index (int, optional): The index of the attachment to download.
                                         Defaults to 0 (first attachment).
    
    Returns:
        str: The path to the downloaded file, or None if download failed.
    """
    # Initialize the client
    client = ConfluenceClient()

    # Get the attachment info
    attachments = client.get_page_attachments(page_id)
    
    if not attachments:
        print(f"No attachments found for page {page_id}")
        return None
    
    if attachment_index >= len(attachments):
        print(f"Attachment index {attachment_index} out of range. Only {len(attachments)} attachments available.")
        return None
    
    attachment = attachments[attachment_index]
    download_link = attachment.get('_links', {}).get('download')
    
    if not download_link:
        print(f"No download link found for attachment")
        return None
    
    # Get the filename
    filename = attachment.get('title', 'unknown_file')
    
    # Construct the correct download URL
    base_url = client.credentials.get('url') + '/wiki'
    download_url = base_url + download_link

    # Create the output directory if specified
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
        file_path = os.path.join(output_dir, filename)
    else:
        file_path = filename

    # Download the attachment
    response = requests.get(
        download_url,
        auth=(client.credentials.get('email'), client.credentials.get('api_token')),
        stream=True
    )

    if response.status_code == 200:
        with open(file_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        print(f'Download successful: {file_path}')
        return file_path
    else:
        print(f'Error downloading attachment: HTTP {response.status_code}')
        return None


def main():
    """Command line interface for downloading attachments."""
    parser = argparse.ArgumentParser(description='Download attachments from Confluence')
    parser.add_argument('page_id', help='The ID of the Confluence page')
    parser.add_argument('--output-dir', '-o', help='Directory to save the attachment to')
    parser.add_argument('--attachment-index', '-i', type=int, default=0,
                        help='Index of the attachment to download (default: 0, first attachment)')
    
    args = parser.parse_args()
    
    download_attachment(args.page_id, args.output_dir, args.attachment_index)


if __name__ == '__main__':
    main() 