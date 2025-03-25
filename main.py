from image_search import *
from layout_manager import *
from slides_builder import *
from scripter import *
from text2speech import *
from video import *
import json
from utility_functions import *


def main():
    import time
    # Start the timer
    start_time = time.time()

    #API Keys:
    groq_api_key = open('cred/apikeys.txt').readlines()[0].strip() #groq
    ELEVENLABS_API_KEY = open('cred/apikeys.txt').readlines()[1].strip() #elevenlabs
    serpapikey = open('cred/apikeys.txt').readlines()[2].strip() #serpapi
    # Define the LLM client, model and API keys
    from openai import OpenAI   
    client = OpenAI(
        base_url="https://api.groq.com/openai/v1",
        api_key=groq_api_key
    )
    groqmodel = "llama3-8b-8192"

    #! INPUTS
    # Define the variables for the f-string
    topic = input("Enter the topic of your presentation: ")
    comments = input("Enter any comments or suggestions for the presentation (optional): ")

    #! CREATE DIRECTORIES
    os.makedirs('out', exist_ok=True)
    os.makedirs('img', exist_ok=True)
    os.makedirs('outvoices', exist_ok=True)
    os.makedirs('outimages', exist_ok=True)

    #! IMAGE SEARCH
    print("===================================")
    print("          IMAGE SEARCHING STAGE     ")
    print("===================================")
    # Create the queries
    print(f"Asking the LLM to generate queries for {topic}...")
    queries = LLM_queries(groqmodel, client, topic, comments, num_queries = 4)

    #Print the queries
    print("Generated Queries:")
    for i, query in enumerate(queries, start=1):
        print(f"{i}: {query}")
    
    #Get the thumbnails
    print("Downloading the thumbnails...")
    choices = []
    for query in queries:
        images = search(query, serpapikey)
        mask = [True]*5 #Take the first 5 images
        paths_downloads = save_images(query, mask, images, thumbnails = True, folder_dir = 'img')
        #This thumbnails will be shown to choose from
        choices.append([False]*len(paths_downloads))
    
    print("Choosing the images.")
    # Choose the images
    for query_choice in choices:
        query_choice[0] = True #Take the first image of each query

    #Get the images
    print("Downloading the chosen images...")
    path_images = []
    for query, choice in zip(queries, choices):
        paths = save_images(query, choice, thumbnails = False, folder_dir = 'img')
        path_images.extend(paths)

    #Get descriptions of images
    img_dict = write_img_dict(path_images, client)

    image_desc = [img_dict[path] for path in path_images]
    #! BUILD LAYOUT
    print("===================================")
    print("          LAYOUT BUILDING STAGE    ")
    print("===================================")
    while True:
        try:
            duration = int(input("Enter the desired duration of your presentation in minutes: "))
            break
        except ValueError:
            print("Invalid input. Please enter an integer for the duration.")
    

    # Pressing enter also means y
    include_title = request_choice(request="Include title slide? (y/n): ", replies_list=["y", "n", ""]) != "n"
    include_index = request_choice(request="Include index slide? (y/n): ", replies_list=["y", "n", ""]) != "n"
    include_title_sections = request_choice(request="Include title sections? (y/n): ", replies_list=["y", "n", ""]) != "n"

    print("Building the layout for the slides...")
    try:
        indices, descriptions = build_layout_groq(client, groqmodel, topic, duration, comments, include_title, include_index, include_title_sections, image_desc)
    except Exception as e:
        print(f"\n{e}\n")
        while True:
            retry = input("Do you want to retry building the layout? (y/n): ").strip().lower()
            if retry == 'y':
                print("Building the layout for the slides...")
                try:
                    indices, descriptions = build_layout_groq(client, groqmodel, topic, duration, comments, include_title, include_index, include_title_sections, image_desc)
                    break  # Exit the loop if successful
                except Exception as e:
                    print(f"\n{e}\n")
            elif retry == 'n':
                print("Interrupting execution.")
                return
            else:
                print("Invalid input. Please enter 'y' or 'n'.")
    print("Saving the indices and descriptions of the layout to out/out.txt")
    save_layout_prompt(indices, descriptions)

    print("Finding which slides contain which images...")
    images = find_img_in_slides(img_dict, descriptions) #get which images are in which slides
    with open("out/img_dict.json", "w") as img_dict_file:
        json.dump(img_dict, img_dict_file)
    
    with open("out/images_in_slides.json", "w") as images_file:
        json.dump(images, images_file)
    print("Creating a presentation with the images and the layout...")
    prs = build_presentation(indices, images) #Create the ppt with the images
    print("Adding text to the slides according to their descriptions...")
    prs = add_content(prs, indices, descriptions) #Addind the text to the images
    print("Saving the pptx file to out/output.pptx")
    presentation_path = "out/output.pptx"
    prs.save(presentation_path)


    #! WRITING THE SCRIPTS
    print("===================================")
    print("          SCRIPTING STAGE          ")
    print("===================================")
    comments = input("Add any additional comments for the script of the voice:\n")
    print("Writing the script for each slide...")
    scripts = scripter(presentation_path, comments)

    with open("out/script.txt", "w") as f:
        for i, script in enumerate(scripts):
            f.write(f"Slide {i+1}:\n{script}\n\n")
    print("Script saved to out/script.txt")
    print("Here the script could be edited")


    #! GETTING THE AUDIOS
    print("===================================")
    print("          NARRATION STAGE          ")
    print("===================================")
    voice_id = "29vD33N1CtxCmqQRPOHJ"
    for i, script in enumerate(scripts):
        print(f"Processing script for Slide {i+1}...")
        filename = f"Slide{i+1}"
        print(f"Converting script to speech for Slide {i+1}...")
        try:
            ok = text_to_speech(script, ELEVENLABS_API_KEY, voice_id, f"outvoices/{filename}")
        except Exception as e:
            # Ensure the raised object is a byte string and decode it
            if isinstance(e, bytes):
                error_str = e.decode("utf-8")  # Decode bytes to string
                error_data = json.loads(error_str)  # Parse string to JSON
                detail = error_data.get("detail", {})
                status = detail.get("status", "unknown_error")
                message = detail.get("message", "No message provided")
                print(f"Error generating audio for slide {i+1}: \n{status} - {message}")
            else:
                print(f"Unexpected exception: {e}")
            break

    

    #! MAKING THE VIDEO
    print("===================================")
    print("          VIDEO     STAGE          ")
    print("===================================")
    #First we convert all the slides into images
    print("Converting all the slides into images for the video...")
    PPTconvert(presentation_path, "outimages", formatType=18)
    print("Making a simple video...")
    create_simple_video(
        slide_folder='outimages',
        audio_folder='outvoices',
        output_video='out/output_video.mp4',
        silent_duration=5.0,
        transition_duration=0.5
        )

    #stop the time
    end_time = time.time()
    time_taken = end_time - start_time
    minutes, seconds = divmod(time_taken, 60)
    print(f"Time taken for the entire process: {int(minutes)}:{seconds:.2f} min:secs")

if __name__ == "__main__":
    main()