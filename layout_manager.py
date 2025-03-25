from utility_functions import *
import json
import openai


def build_layout_groq(client, groqmodel: str, topic: str, duration: float, comments: str, include_title: bool, include_index: bool, include_title_sections: bool, images = None) -> tuple[list, list]:
    # Defining the prompt
    prompt = f"""
    Presentation context:

    Topic of the presentation: {topic}

    Duration: {duration} mins.

    For building the layout you have the following types of slides. The indices distinguish each type of slide layout:

    """
    if include_title:
        prompt += f"""Title (index 0): Just for the title of the presentation.\n"""
    if include_title_sections:
        prompt += f"""Section title (index 2): For the title of each section when they start. It does not include content apart from the title.\n"""

    prompt += f"""Content: 
        - Ideas in bullet points (index 1).
        - Comparison in 2 columns (index 4).\n"""

    if images is not None:
        prompt += f"""Pictures:
        - If there is only one image (index 8). ONLY ONE IMAGE IN THIS SLIDE TYPE.
        - If there are between two and four images (index 5). ONLY MULTIPLE IMAGES IN THIS SLIDE TYPE.
        In these picture slides (either of one or multiple images format), you MUST fit ONLY following images (make sure to reference each image name correctly in the description of the corresponding slide):\n"""
        for image in images:
            prompt +=f"- {image}\n"

    prompt += f"""\nNow, taking into account that a title slide takes about 15 seconds, a picture/plot slide takes about 30 seconds and a content slide takes about 45 seconds, build a layout for well structured slide presentation.

    Comments and suggestions:
    {comments}

    WARNING: DO NOT INVENT ANY IMAGE NAMES, USE ONLY THE IMAGE NAMES THAT ARE PROVIDED IN THIS PROMPT. REMEMBER INDICES MEAN A CERTAIN LAYOUT FOR THE SLIDE, DO NOT USE THEM FOR ENUMERATING SLIDES.
    Return the layout as a JSON object with the following schema:
    ```json
    {{"slides": [{{"index": index, "description": "description"}}, ... ]}}
    ```
    """

    # Defining the sysprompt
    sysprompt = "You are an expert in creating structured slide presentations. Based on the provided context, design a complete slide layout that fits within the specified duration and uses the slide types available. Each slide must include a very detailed description of its content or purpose. Ensure the presentation flows logically, with the right balance of contents while adhering to the timing constraints provided. Return the layout as a list of slide objects with the index and description. Notice that ALL the slides have a title referring to the section, subsection or content of the slide itself so the description has to make clear what the title of each slide could be. Also indices mean a certain template, NOT a position of the slide. YOU ARE ONLY ALLOWED TO USE THE IMAGES THAT ARE SPECIFIED TO YOU IN THE PROMPT AND YOU WILL REFERENCE TO THEM WITH THE SAME NAME AS IN THE PROMPT"

    # Call the API with structured response format
    try: 
        completion = client.chat.completions.create(
            model=groqmodel,
            messages=[
                {"role": "system", "content": sysprompt},
                {"role": "user", "content": prompt},
            ],
            response_format={"type": "json_object"},
        )
    except openai.BadRequestError as e:
        raise Exception(f"Error code: {e.error['code']} - {e.error['message']}")

    # Extract the parsed message from the response
    slides = completion.choices[0].message.content
    slides = json.loads(slides)["slides"]

    # Initialize empty lists to store indices and descriptions
    indices = []
    descriptions = []

    # Iterate through the parsed slides and populate the lists
    for slide in slides:
        indices.append(slide["index"])
        descriptions.append(slide["description"])


    # Iterate until the estimated duration is the correct one.
    for i in range(3): # Just give it 3 tries more to fix it
        warnings = "\n Aspects to fix about the previous layout:" #This string has lenght 43
        if 0 in indices[1:]:
            zero_index = indices.index(0, 1)
            warnings = f"\nTitle of the presentation slide (index 0) should only be at the beginning of the presentation. Please correct the layout."
        
        estimated_duration = estimate_duration(indices)
        if abs(estimated_duration - duration) > 2:
            warnings = f"\nThe estimated duration is {estimated_duration} mins which is too far from the {duration} mins requested. Please adjust the layout to fit the requested duration."

        if len(warnings) > 43:
            print(f"Trying to fix the output to match the warnings. Attempt {i}")
            previous_layout = "\nPrevious Layout:"
            for index, description in zip(indices, descriptions):
                previous_layout += f"\n- {{'index': {index}, 'description': '{description}'}}"

            try:
                completion = client.chat.completions.create(
                    model=groqmodel,
                    messages=[
                        {"role": "system", "content": sysprompt},
                        {"role": "user", "content": prompt + previous_layout + warnings}, #Adding the comments to the prompt
                    ],
                    response_format={"type": "json_object"},
                )
            except openai.BadRequestError as e:
                raise Exception(f"Error code: {e.error['code']} - {e.error['message']}")

            # Extract the parsed message from the response
            slides = completion.choices[0].message.content
            slides = json.loads(slides)["slides"]

            # Initialize empty lists to store indices and descriptions
            indices = []
            descriptions = []

            # Iterate through the parsed slides and populate the lists
            for slide in slides:
                indices.append(slide["index"])
                descriptions.append(slide["description"])

    if include_index:
        info = ""
        for i in range(len(descriptions)):
            info += f"Slide {i}: {descriptions[i]}\n"
        index_prompt = f"Create a slide index for a presentation with the following slides:\n{info}"
        index = client.chat.completions.create(
            model=groqmodel,
            messages=[
                {"role": "system", "content": "You are an expert in creating slide indexes. Create a slide index based on the provided list of slide descriptions. Only answer with the index."},
                {"role": "user", "content": index_prompt},
            ]
        )
        
    if 0 in indices:
        zero_index = indices.index(0)
        indices.insert(zero_index + 1, 11)
        descriptions.insert(zero_index + 1, index.choices[0].message.content)
    else:
        indices.insert(0, 11)
        descriptions.insert(0, index.choices[0].message.content)

    return indices, descriptions






if __name__ == "__main__":
    groqmodel = "llama3-8b-8192"
    groq_api_key = open('cred/apikeys.txt').readlines()[0].strip() #groq
    from openai import OpenAI   
    client = OpenAI(
        base_url="https://api.groq.com/openai/v1",
        api_key=groq_api_key
    )
    # Define the variables for the f-string
    topic = input("Enter the topic of your presentation: ")
    while True:
        try:
            duration = int(input("Enter the desired duration of your presentation in minutes: "))
            break
        except ValueError:
            print("Invalid input. Please enter an integer for the duration.")
    comments = input("Enter any comments or suggestions for the presentation (optional): ")

    # Pressing enter also means y
    include_title = request_choice(request="Include title slide? (y/n): ", replies_list=["y", "n", ""]) != "n"
    include_index = request_choice(request="Include index slide? (y/n): ", replies_list=["y", "n", ""]) != "n"
    include_title_sections = request_choice(request="Include title sections? (y/n): ", replies_list=["y", "n", ""]) != "n"

    images = ["Foreo_Luna_Comparison", "Foreo_Logo", "Foreo_growth_plot", "Face_cleansing_device"]

    indices, descriptions = build_layout_groq(client, groqmodel, topic, duration, comments, include_title, include_index, include_title_sections, images)

    output = ""
    for i, d in zip(indices, descriptions):
        output += f"Slide {i}: {d}\n"
    print(f"Output is: \n {output}")
    print(f"Indices: \n{indices}")
    print(f"Descriptions: \n{descriptions}")

    with open("out.txt", "w") as f:
        f.write(output)