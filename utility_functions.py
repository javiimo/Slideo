import os
import json

def save_layout_prompt(indices, descriptions):
    output = ""
    for i, d in zip(indices, descriptions):
        output += f"Slide {i}: {d}\n"
    print(f"Output is: \n {output}")
    print(f"Indices: {indices}")
    print(f"Descriptions: {descriptions}")

    with open("out/out.txt", "w") as f:
        f.write(output)


def request_choice(request: str, replies_list: list):
    while True:
        user_input = input(request)
        if user_input in replies_list:
            return user_input
        else:
            print("Invalid input. Please try again.")


def estimate_duration(index_list) -> float:
    """Estimates the duration of a presentation based on the indices of its slides.

    Args:
        index_list: A list of integers representing the indices of the slides in the presentation layout.

    Returns:
        The estimated duration of the presentation in minutes.
    """
    duration_estimation_dict = {
        0: 15, #title
        11: 30, #index
        1: 45, #content
        2: 15, #section title
        4: 45, #content
        5: 30, #images
        8: 30  #images
    }
    seconds = 0
    for index in index_list:
        seconds += duration_estimation_dict.get(index, 0)  # Use get with default 0 for unknown indices

    minutes = seconds / 60
    return minutes



def get_thumbnails_dict(folder_dir='img'):
    thumbnails_dict = {}
    
    # Iterate through each query folder in img directory
    for query_folder in os.listdir(folder_dir):
        folder_path = os.path.join(folder_dir, query_folder)
        
        # Skip if not a directory
        if not os.path.isdir(folder_path):
            continue
            
        # Get list of thumbnail files in this query folder
        thumbnail_paths = []
        for filename in os.listdir(folder_path):
            if filename.startswith('thumbnail_'):
                full_path = os.path.join(folder_dir, query_folder, filename)
                thumbnail_paths.append(full_path)
                
        # Add to dictionary if thumbnails were found
        if thumbnail_paths:
            thumbnails_dict[query_folder] = thumbnail_paths
            
    return thumbnails_dict


def delete_non_thumbnail_images(folder_dir='img'):
    # Iterate through each query folder in the specified directory
    for query_folder in os.listdir(folder_dir):
        folder_path = os.path.join(folder_dir, query_folder)
        
        # Skip if not a directory
        if not os.path.isdir(folder_path):
            continue
        
        # Iterate through each file in the query folder
        for filename in os.listdir(folder_path):
            # Check if the file does not start with 'thumbnail_' and is not a json file
            if not filename.startswith('thumbnail_') and not filename.endswith('.json'):
                full_path = os.path.join(folder_path, filename)
                try:
                    os.remove(full_path)  # Delete the file
                    print(f"Deleted: {full_path}")
                except Exception as e:
                    print(f"Error deleting {full_path}: {e}")



def get_jsons_dict(folder_dir='img'):
    jsons_dict = {}
    
    # Iterate through each query folder in img directory
    for query_folder in os.listdir(folder_dir):
        folder_path = os.path.join(folder_dir, query_folder)
        
        # Skip if not a directory
        if not os.path.isdir(folder_path):
            continue
            
        # Get the json file path
        json_path = os.path.join(folder_path, 'query.json')
        
        # Skip if json file doesn't exist
        if not os.path.exists(json_path):
            continue
            
        # Read and parse the json file
        try:
            with open(json_path, 'r') as f:
                json_data = json.load(f)
                jsons_dict[query_folder] = json_data
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Error loading JSON for {query_folder}: {e}")
            continue
                
    return jsons_dict


def get_layout_prompt(file_path='out/descriptions.txt'):
    indices = []
    descriptions = []
    current_description = []
    current_index = None
    
    try:
        with open(file_path, 'r') as f:
            lines = f.readlines()
            
        for line in lines:
            if line.strip():  # Skip empty lines
                # Check if line starts a new slide
                if line.startswith('Slide '):
                    # Save previous slide if exists
                    if current_index is not None:
                        indices.append(current_index)
                        descriptions.append(' '.join(current_description))
                    
                    # Start new slide
                    parts = line.split(': ', 1)
                    if len(parts) == 2:
                        current_index = int(parts[0].replace('Slide ', ''))
                        current_description = [parts[1].strip()]
                else:
                    # Append to current description if not a new slide
                    if current_index is not None:
                        current_description.append(line.strip())
        
        # Add final slide
        if current_index is not None:
            indices.append(current_index)
            descriptions.append(' '.join(current_description))
                        
        return indices, descriptions
        
    except Exception as e:
        print(f"Error reading layout prompt file: {e}")
        return [], []

def get_scripts(file_path="out/script.txt"):
    scripts = []
    current_script = []
    with open(file_path, "r") as f:
        lines = f.readlines()
        for line in lines:
            if line.startswith("Slide "):
                if current_script:
                    scripts.append("".join(current_script))
                    current_script = []
            else:
                current_script.append(line)
        if current_script:  # Add the last script
            scripts.append("".join(current_script))
    return scripts