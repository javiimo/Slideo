## layout_manager.py

We use a prompt to get the indices 

prompt:
    Presentation context:

    Topic of the presentation: {topic}

    Duration: {duration} mins.

    For building the layout you have the following types of slides. The indices distinguish each type of slide layout:

    **if include_title:**
        prompt += f"""Title (index 0): Just for the title of the presentation.\n"""
    **if include_title_sections:**
        prompt += f"""Section title (index 2): For the title of each section when they start.\n"""

    Content: 
        - Ideas in bullet points (index 1).
        - Comparison in 2 columns (index 4).

    **if include_image_slides:**
        prompt += f"""Pictures/plots:
        - If there is only one image (index 8)
        - If there are more than one images (index 5)\n"""

    Now, taking into account that a title slide takes about 15 seconds, a picture/plot slide takes about 30 seconds and a content slide takes about 45 seconds, build a layout for well structured slide presentation.

    Comments and suggestions:
    {comments}


    Return the layout as a JSON object with the following schema:
    ```json
    {{"slides": [{{"index": index, "description": "description"}}, ... ]}}
    ```
    """


sysprompt = "You are an expert in creating structured slide presentations. Based on the provided context, design a complete slide layout that fits within the specified duration and uses the slide types available. Each slide must include a very concise description of its content or purpose. Ensure the presentation flows logically, with the right balance of contents while adhering to the timing constraints provided. Return the layout as a list of slide objects with the index and description. Notice that ALL the slides have a title referring to the section, subsection or content of the slide itself so the description has to make clear what the title of each slide could be. Also indices mean a certain template, NOT a position of the slide."


Indices:
"""
0 : Title
2 : Section Title
1 : Content in bullet points
4 : Content comparison in 2 columns
8 : Only one image
5 : More than one image
11 : Index
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





## slides_builder.py

Build the presentation

Add content to each slide (according to its type) by giving the context of the description to the LLM.

There is an example of the descriptions and indices in the if name==main


## scripter.py

Takes all the text from a slide and the first image (because groq API only supports 1 image per call) and generates a script. It accepts additional comments that we might give to the LLM like having a certain tone or being more concise or using certain expressions or whatever.

The prompt is as follows:

sysprompt = "You are an expert narrator script writer. You will receive information extracted from slides, including text and one image (if there is one in the slide). Your task is to create a compelling and informative script for a narrator that explains the slide's content without directly reading the text. Instead, focus on providing context, insights, and connections between the different elements on the slide. If images are present, refer to them generally in your script (e.g., 'as you can see in the accompanying chart...' or 'the image illustrates...'), if there are none, do not say anything about them. Your script should sound natural, engaging, and suitable for a presentation. DO NOT HALLUCINATE INFORMATION, STICK TO THE INFO IN THE SLIDE."


if extracted_data["text"]:
            prompt += "Text contained in the slide:\n" + "\n".join(extracted_data["text"]) + "\n"
        if comments:
            prompt += "Comments and suggestions about the script:\n" + comments + "\n" #Adding the comments to the prompt


prompt += """Provide the narrator script directly without any introductory or concluding remarks (e.g., 'Here's the script...') or other additions like stage directions (e.g., '(a brief pause)').  Do not include anything else, just the script.
        
        Adjust the time of narration to the type of slide you are presenting. For slides that only show a section title, keep it brief and seamless, simply introducing the section. For content slides, provide more detailed explanations and insights, paraphrasing the information contained in the slide to enhance clarity. Ensure everything you say is grounded in the slide's content.
        """

