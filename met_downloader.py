import requests
import json
import os
import csv
import glob

# MET API endpoint
base_url = "https://collectionapi.metmuseum.org/public/collection/v1/"

def get_last_image_number():
    existing_images = glob.glob("iran_image_*.jpg")
    if not existing_images:
        return 0
    numbers = [int(filename.split('_')[2].split('.')[0]) for filename in existing_images]
    return max(numbers)

def search_and_download(search_term, num_images):
    # Search for items
    search_url = f"{base_url}search?q={search_term}&hasImages=true"
    response = requests.get(search_url)
    search_results = json.loads(response.text)

    last_number = get_last_image_number()
    downloaded = 0
    metadata = []

    # Load existing metadata if CSV exists
    csv_filename = 'image_metadata.csv'
    existing_object_ids = set()
    if os.path.exists(csv_filename):
        with open(csv_filename, 'r', newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            existing_object_ids = set(row.get('object_id', '') for row in reader)

    for object_id in search_results['objectIDs']:
        if downloaded >= num_images:
            break

        # Skip if object ID already processed
        if str(object_id) in existing_object_ids:
            continue

        # Get object details
        object_url = f"{base_url}objects/{object_id}"
        object_response = requests.get(object_url)
        object_data = json.loads(object_response.text)

        # Check if the object has a primary image
        if object_data.get('primaryImage'):
            image_url = object_data['primaryImage']
            filename = f"iran_image_{last_number + downloaded + 1}.jpg"
            
            # Download the image
            image_response = requests.get(image_url)
            if image_response.status_code == 200:
                full_path = os.path.abspath(filename)
                with open(full_path, 'wb') as f:
                    f.write(image_response.content)
                print(f"Downloaded: {full_path}")

                # Collect metadata
                metadata.append({
                    'image_id': filename,
                    'object_id': str(object_id),
                    'title': object_data.get('title', 'Unknown'),
                    'artist': object_data.get('artistDisplayName', 'Unknown'),
                    'date': object_data.get('objectDate', 'Unknown'),
                    'period': object_data.get('period', 'Unknown'),
                    'culture': object_data.get('culture', 'Unknown'),
                    'medium': object_data.get('medium', 'Unknown'),
                    'dimensions': object_data.get('dimensions', 'Unknown'),
                    'department': object_data.get('department', 'Unknown'),
                    'object_type': object_data.get('objectName', 'Unknown'),
                    'object_url': object_data.get('objectURL', 'Unknown')
                })

                downloaded += 1

    print(f"Downloaded {downloaded} new images related to {search_term}")
    
    # Append new metadata to CSV
    mode = 'a' if os.path.exists(csv_filename) else 'w'
    with open(csv_filename, mode, newline='', encoding='utf-8') as csvfile:
        fieldnames = metadata[0].keys() if metadata else None
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        if mode == 'w':
            writer.writeheader()
        for row in metadata:
            writer.writerow(row)
    print(f"Metadata appended to {csv_filename}")

# Usage
search_and_download("Iran", 5)