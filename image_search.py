import serpapi
import os
import urllib.request
import urllib.parse
from urllib.error import URLError, HTTPError
import io
from PIL import Image
import json
from io import BytesIO
import base64


def search(query: str, api_key: str):
    params = {
        "engine": "google_images",
        "q": query,
        "api_key": api_key
    }

    try:
        search = serpapi.search(params)
        results = search.as_dict()
    except Exception as e:
        print(f"Error during search: {e}")
        return []

    images = []
    for image in results.get("images_results", []):
        title = image.get("title", "untitled").replace(" ", "_").replace("/", "_").replace("\\", "_").replace(":", "_").replace("*", "_").replace("?", "_").replace("\"", "_").replace("<", "_").replace(">", "_").replace("|", "_")
        original_width = image.get("original_width", 0)
        original_height = image.get("original_height", 0)
        link = image.get("original", "")
        thumbnail = image.get("thumbnail", "")
        
        if link and thumbnail:
            image_name = f"{title}_{original_width}x{original_height}.jpg"
            images.append({"name": image_name, "link": link, "thumbnail": thumbnail})
    
    return images


def save_json_query(folder_path, images = None):
    # Create the directory if it doesn't exist
    os.makedirs(folder_path, exist_ok=True)
    # Save the images dictionary as query.json in the folder_path
    with open(os.path.join(folder_path, 'query.json'), 'w') as json_file:
        json.dump(images, json_file, indent=4)
    return

def load_json_query(folder_path):    
    # Load the images dictionary from query.json in the folder_path
    with open(os.path.join(folder_path, 'query.json'), 'r') as json_file:
        images = json.load(json_file)
    
    return images


def save_images(query: str, images = None, ref_names = [], num = 1, thumbnails: bool = False, folder_dir: str = 'img') -> list:
    """
    Download and save images from URLs, with validation.
    
    Args:
        images: List of dictionaries containing image info with 'name', 'link' and 'thumbnail' keys. Each image is a dictionary of this list
        query: String to name the subfolder
        ref_names: the list of images that are already downloaded or the ones that need to be downloaded.
        thumbnails: Boolean indicating whether to download the thumbnail (lower resolution) if True or the original image (higher resolution) 
        init_index = This is the first index in the list of searched images that we download.
        end_index = This is the last index in the list of searched images that we download.
        folder_dir: Base directory for saving images
        
    Returns:
        list: List of successfully downloaded image paths
    """
    query = "".join(c for c in query if c.isalnum() or c in (' ', '-', '_')).strip()
    folder_path = os.path.join(folder_dir, query)

    # Save the images dictionary as query.json in the folder_path
    json_path = os.path.join(folder_path, 'query.json')
    try: 
        if (images is not None) and not os.path.exists(json_path):
            save_json_query(folder_path, images)
        elif images is None: #Load the images dictionary from query.json in the folder_path
            images = load_json_query(folder_path)
        else:
            raise Exception("No images dictionary given and no json file found for that query")
    except Exception as e:
        print(f"Error loading/saving JSON: {e}")
        return []

    if ref_names == []:
        ref_ind = 0
        short_list = images[ref_ind:ref_ind + num]
    else:
        list_ref_ind = []
        for ref in ref_names:
            print(f"Ref is {ref}")
            for i, image in enumerate(images):
                print(image['name'])
                found = fuzzy_substring_match(image['name'], ref, tolerance=0.8)
                if found:
                    list_ref_ind.append(i)
                    break
        ref_ind = max(list_ref_ind)   
        if num > 1:
            short_list = images[ref_ind+1:ref_ind + num+1] #+1 is to skip the ref name image
        else:
            short_list = images[ref_ind:ref_ind + num]
                    

    if not 'ref_ind' in locals():
        print("Didn't find an image with that name in the json")
        return []
    

    successful_downloads = []
    
    for image in short_list:
        # Sanitize filename
        safe_name = "".join(c for c in image['name'] if c.isalnum() or c in ('-', '_', '.')).strip()
        if not safe_name.lower().endswith(('.jpg', '.jpeg', '.png', '.gif')):
            safe_name += '.jpg'
        
        if thumbnails:
            safe_name = 'thumbnail_' + safe_name
            
        image_path = os.path.join(folder_path, safe_name)

        try:
            # Encode URL properly
            if thumbnails:
                encoded_url = urllib.parse.quote(image['thumbnail'], safe=':/?=&')
            else:
                encoded_url = urllib.parse.quote(image['link'], safe=':/?=&')
            
            # Download with a timeout and user agent
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
            request = urllib.request.Request(encoded_url, headers=headers)
            
            with urllib.request.urlopen(request, timeout=10) as response:
                image_data = response.read()
                
                # Verify it's actually an image              
                image_data_stream = io.BytesIO(image_data)
                try:
                    with Image.open(image_data_stream) as img:
                        img.verify()  # Verify that it is an image
                        image_type = img.format.lower()  # Get the image format
                except Exception:
                    image_type = None
                
                if image_type is None:
                    print(f"Downloaded file is not a valid image: {safe_name}")
                    continue
                    
                # Save the verified image
                with open(image_path, 'wb') as f:
                    f.write(image_data)
                    
                successful_downloads.append(image_path)
                print(f"Successfully downloaded: {safe_name}")
                
        except HTTPError as e:
            print(f"HTTP Error for {safe_name}: {e.code} {e.reason}")
        except URLError as e:
            print(f"URL Error for {safe_name}: {e.reason}")
        except TimeoutError:
            print(f"Timeout downloading {safe_name}")
        except Exception as e:
            print(f"Error saving {safe_name}: {str(e)}")
            
    return successful_downloads



def LLM_queries(groqmodel, client, topic, comments, num_queries = 3):
    sysprompt = "You are an expert in generating effective Google search queries for finding images suitable for presentations. Your task is to create queries that are concise, varied and relevant to the given topic. The queries should be formatted as if they are being typed directly into the Google search bar, without any additional formatting, HTTP requests, or unusual syntax. Focus on clarity and specificity to ensure the best results for image searches. Write your structured answers in JSON format."

    prompt = f"""Write EXACTLY {num_queries} google search querie(s) for finding useful images for a presentation. Do not write more or less than the number of queries requested. Exactly that number please. Here is the information about the presentation:

    The topic is: {topic}

    Also the user added the following comments about the presentation, that might or might not contain useful information for writing proper queries:
    {comments}

    Return the queries (exactly the number of queries requested above, no more and no less) as a JSON object with the following schema:
    ```json
    {{"queries": ["query 1", "query 2",...]}}
    ```
    """
    completion = client.chat.completions.create(
        model=groqmodel,
        messages=[
            {"role": "system", "content": sysprompt},
            {"role": "user", "content": prompt},
        ],
        response_format={"type": "json_object"},
    )

    # Extract the parsed message from the response
    queries = completion.choices[0].message.content
    queries = json.loads(queries)["queries"]

    return queries[:num_queries]


def describe_image(client, image_path, model="llama-3.2-11b-vision-preview"):
    """
    Describe an image using a language model.

    This function takes an image path and a client for the language model, 
    processes the image to generate a base64 representation, and sends a 
    request to the model to obtain a concise description of the image. 
    The description is limited to 1 to 3 words, capturing the essence of 
    the image for better understanding without visual reference.

    Args:
        client: The client instance for interacting with the language model.
        image_path (str): The file path of the image to be described.
        model (str): The model to be used for generating the description. 
                     Defaults to "llama-3.2-11b-vision-preview".

    Returns:
        str: A concise description of the image, formatted with underscores 
             instead of spaces.
    """

    sysprompt = """You are an advanced image analysis model. Your task is to provide concise and accurate descriptions of images based on their visual content. The descriptions should be limited to 1 to 3 words, capturing the essence of the image in a way that allows someone unfamiliar with it to understand its content without needing to view it. Focus on key elements, in the image and overall topic, ensuring clarity and specificity in your responses. 
    USEFUL INFORMATION YOU MUST ADD:
    It is interesting to tell image format: a plot, a picture, a diagram, etc.
    Names, brands, most relevant elements,... might be useful as well"""

    image_name = image_path.split("/")[-1]  # Get the name of the image file from image_path
    prompt = f"""Generate a brief description of the image in 2 to 4 words maximum (the fewer the better) that captures its core essence, enabling someone who has not seen the image to grasp its content. Be as detailed as possible withing the limited extension. Answer only with the 2 to 4 words description, without any weird formating or bold or anything, just plain text. 
    ALWAYS ADD THE FORMAT OF THE IMAGE: plot, picture, diagram, comparison, histogram, chart,...
    ALWAYS ADD ANY BRANDS OR NAMES THAT IDENTIFY THE MAIN ELEMENT(S) OF THE IMAGE.
    For more context, the image filename is {image_name}. It might contain useful information about the image content."""

    # Open the image file
    with open(image_path, "rb") as img_file:
        image_bytes = img_file.read()
    
    # Convert to JPEG if not already
    if not image_path.lower().endswith(".jpg"):
        image_pil = Image.open(BytesIO(image_bytes))
        buffered = BytesIO()
        image_pil.save(buffered, format="JPEG")
        image_bytes = buffered.getvalue()

    # Convert to base64
    image_base64 = base64.b64encode(image_bytes).decode('utf-8')

    messages = [
        {
            "role": "user", 
            "content": [
                {"type": "text", "text": sysprompt +"\n"+ prompt}, 
                {
                    "type": "image_url", 
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{image_base64}",
                    },
                },
            ],
        }
    ]


    completion = client.chat.completions.create(
        model=model,
        messages=messages
    )
    content = completion.choices[0].message.content
    content = content.replace(" ", "_").replace(".","").replace("\n","").lower()

    return content

def write_img_dict(image_paths, client):
    """
    Generates a dictionary mapping image paths to their corresponding descriptions.

    Args:
        image_paths (list): A list of paths to the images to be described.
        client: The OpenAI client used to generate descriptions.

    Returns:
        dict: A dictionary where keys are image paths and values are their respective descriptions.
    """
    dict = {}

    for image in image_paths:
        description = describe_image(client, image, model="llama-3.2-11b-vision-preview")
        dict[image] = description

    return dict


def fuzzy_substring_match(text, pattern, tolerance=0.8):
    """
    Check if pattern appears in text with smart character skipping.
    
    Args:
        text (str): The longer text to search in
        pattern (str): The shorter string to search for
        tolerance (float): Minimum ratio of matching characters (0.0 to 1.0)
    """
    text = text.lower()
    pattern = pattern.lower()
    
    if len(pattern) == 0:
        return False
    
    best_match_count = 0
    
    # Try matching starting from each position in text
    for start_pos in range(len(text)):
        matches = 0
        consecutive_errors = 0
        pattern_pos = 0
        i = start_pos
        
        while i < len(text) and pattern_pos < len(pattern):
            if text[i] == pattern[pattern_pos]:
                matches += 1
                consecutive_errors = 0
                pattern_pos += 1
                i += 1
            else:
                # Try looking ahead in pattern for a match
                found_next = False
                if pattern_pos + 1 < len(pattern):
                    # Check if next pattern char matches current text char
                    if text[i] == pattern[pattern_pos + 1]:
                        pattern_pos += 2  # Skip the missing char and move past the matched one
                        matches += 1      # Count the match we found
                        consecutive_errors = 0
                        i += 1
                        found_next = True
                
                if not found_next:
                    consecutive_errors += 1
                    if consecutive_errors > 2:
                        break
                    i += 1  # Move to next text character but keep same pattern position
            
        best_match_count = max(best_match_count, matches)
    
    match_ratio = best_match_count / len(pattern)
    return match_ratio >= tolerance

def find_img_in_slides(img_dict, descriptions):
    """
    Maps slide descriptions to corresponding image paths, returning a list of lists 
    where each sublist contains paths for images in a slide.
    """
    image_paths = []
    
    for desc in descriptions:
        slide_images = []
        for image_path, image_desc in img_dict.items():
            if fuzzy_substring_match(desc, image_desc, tolerance=0.8):
                slide_images.append(image_path)
        image_paths.append(slide_images)
    
    return image_paths





if __name__ == "__main__":  
    from openai import OpenAI
    with open("cred/apikeys.txt", "r") as f:
        groq_api_key = f.readline().strip()

    client = OpenAI(
        base_url="https://api.groq.com/openai/v1",
        api_key=groq_api_key
    )
    groqmodel = "llama3-8b-8192"
    # topic = input("Topic: ")
    # comments = input("Comments: ")

    # queries = LLM_queries(groqmodel, client, topic, comments, num_queries = 3)

    # serpapikey = open('cred/apikeys.txt').readlines()[2].strip()
    # for query in queries:
    #     images = search(query, serpapikey)
    #     paths_downloads = save_images(query, images, thumbnails = False, 
    #                                   init_index = 0, end_index = 10, folder_dir = 'img')
    #     print(paths_downloads)

    image_path = r"img\smart beauty gadgets foreo products images\thumbnail_FOREO_LUNA_4_Face_Cleansing_Brush_..._2000x2000.jpg"
    desc = describe_image(client, image_path, model="llama-3.2-11b-vision-preview")

    print(desc)