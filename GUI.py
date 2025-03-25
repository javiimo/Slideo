#streamlit run GUI.py
#https://medium.com/data-science-in-your-pocket/how-to-convert-streamlit-app-into-exe-executable-file-0e8d1dcbd07f
import streamlit as st
import os
from image_search import *
from layout_manager import *
from slides_builder import *    
from scripter import *
from text2speech import *
from video import *
from cryptography.fernet import Fernet
from streamlit_image_select import image_select
import copy
from openai import OpenAI  
import shutil
import time


#!SIDEBAR-------------------------------------------
#!This is the key for loading/saving the api keys. It isn't safe to store it here. But will leave it here for now
key = b'3w8D5aFvKqYOEVxn3Q4H801CAIdvw3VzM6bEox67B6A='


# Callback function to update session state with loaded keys
def load_keys_from_file(message = True):
    cipher_suite = Fernet(b'3w8D5aFvKqYOEVxn3Q4H801CAIdvw3VzM6bEox67B6A=')
    try:
        with open('config/apikeys.enc', 'rb') as f:
            encrypted_data = f.read()
            # Split the encrypted data into individual encrypted keys
            encrypted_keys = encrypted_data.split(b'gAAAAAB')
            encrypted_keys = [b'gAAAAAB' + key for key in encrypted_keys[1:]]  # Skip empty first split
            
            if len(encrypted_keys) > 0:
                replace_state("groq_key", cipher_suite.decrypt(encrypted_keys[0]).decode('utf-8'))

            if len(encrypted_keys) > 1:
                replace_state("eleven_key", cipher_suite.decrypt(encrypted_keys[1]).decode('utf-8'))

            if len(encrypted_keys) > 2:
                replace_state("serp_key", cipher_suite.decrypt(encrypted_keys[2]).decode('utf-8'))

        #Print which keys are loaded
        if message:
            services = [service for service, key in zip(["Groq", "ElevenLabs", "Search"], encrypted_keys) if key]
            if len(services)>1:
                services = [services[0]] + [", " + service for service in services[1:]]
            st.success(f"API keys for {''.join(services)} loaded successfully!")
    except Exception as e:
        st.error(f"Error loading API keys: {e}")

# Save keys from session state to file
def save_keys_to_file():
    cipher_suite = Fernet(b'3w8D5aFvKqYOEVxn3Q4H801CAIdvw3VzM6bEox67B6A=')
    try:
        with open('config/apikeys.enc', 'wb') as f:
            # Encrypt each key separately
            groq_encrypted = cipher_suite.encrypt(st.session_state.groq_key_input.encode('utf-8'))
            eleven_encrypted = cipher_suite.encrypt(st.session_state.eleven_key_input.encode('utf-8'))
            serp_encrypted = cipher_suite.encrypt(st.session_state.serp_key_input.encode('utf-8'))
            
            # Write all encrypted keys to file
            f.write(groq_encrypted + eleven_encrypted + serp_encrypted)
            
        st.success("API keys were successfully saved and ready to use!")
    except Exception as e:
        st.error(f"Error saving API keys: {e}")


def sidebar():
    st.header("API Configuration")

    # Text input fields for API Keys
    st.text_input("Groq API Key", value=st.session_state.get("groq_key", ""), type="password", key="groq_key_input")
    st.text_input("ElevenLabs API Key", value=st.session_state.get("eleven_key", ""), type="password", key="eleven_key_input")
    st.text_input("SerpAPI Key", value=st.session_state.get("serp_key", ""), type="password", key="serp_key_input")
    
    # Buttons to load or save keys
    if st.button("Load stored keys"):
        load_keys_from_file()
    
    if st.button("Save and load keys"):
        del st.session_state.show_confirm_button
        st.session_state.show_confirm_button = True
        st.error("Are you sure you want to overwrite previous keys with the ones written above?")
    
    if st.session_state.show_confirm_button:
        if st.button("Yes, proceed with saving! 🚀", key = "confirm_button"):
            save_keys_to_file()
            load_keys_from_file(message=False)
        replace_state('show_confirm_button', False)
    
    if st.button("Print Keys"): 
        st.write("Groq API Key:", st.session_state["groq_key"])
        st.write("ElevenLabs API Key:", st.session_state["eleven_key"])
        st.write("SerpAPI Key:", st.session_state["serp_key"])

#! TAB1------------------------------------------------------------------------
def widget2state(state, widget):
    #Note: widget key will be assumed to be always widget+"_input"
    replace_state(state, st.session_state[widget + "_input"])
    st.toast(f"Value of \'{state}\' updated!")


def delete_previous_runs():
    directories = ['out', 'img', 'outvoices', 'outimages']
    for directory in directories:
        if os.path.exists(directory):
            shutil.rmtree(directory)
    create_directories()


#! TAB2------------------------------------------------------------------------
def add_paths(query, num):
    thumbnails_dict = get_thumbnails_dict()
    ref = [ref.split('thumbnail_')[-1] for ref in thumbnails_dict[query]]
    paths = save_images(query, ref_names = ref, num = num, thumbnails = True, folder_dir = 'img') 
    thumbnails_dict[query] = thumbnails_dict[query] + paths
    replace_state("thumbnails_dict", thumbnails_dict)


def widget2state(state, widget):
    #Note: widget key will be assumed to be always widget+"_input"
    replace_state(state, st.session_state[widget + "_input"])
    st.toast(f"Value of \'{state}\' updated!")


def modify(img_path, widget):
    dict = st.session_state.img_dict
    dict[img_path] = st.session_state[widget]
    replace_state('img_dict', dict)
    st.toast("Description updated!")

#! TAB3------------------------------------------------------------------------
#https://pythoninoffice.com/how-to-make-streamlit-multiple-callback/
def edit_desc(widget_key, ind):
    l = st.session_state["descriptions"]
    l[ind] = st.session_state[widget_key]
    replace_state("descriptions", l)
    st.toast("Description updated!")
    #save_layout_prompt(st.session_state.indices, st.session_state.descriptions)

def edit_ind( widget_key, dict, ind):
    l = st.session_state["indices"]
    #From option index to option name with list.
    #From option name to slide index with dict.
    val = dict[st.session_state[widget_key]]
    l[ind] = val
    replace_state("indices", l)
    #save_layout_prompt(st.session_state.indices, st.session_state.descriptions)

def remove_desc_ind(ind):
    ld = st.session_state["descriptions"]
    li = st.session_state["indices"]
    ld.pop(ind)
    li.pop(ind)
    replace_state("descriptions", ld)
    replace_state("indices", li)    
    #save_layout_prompt(st.session_state.indices, st.session_state.descriptions)

def add_desc_ind(ind):
    ld = st.session_state["descriptions"]
    li = st.session_state["indices"]
    ld.insert(ind,"")
    li.insert(ind, 0)#Title slide by default
    replace_state("descriptions", ld)
    replace_state("indices", li)    
    #save_layout_prompt(st.session_state.indices, st.session_state.descriptions)


#! TAB4------------------------------------------------------------------------
#! Update script comments
def edit_script(widget_key, ind):
    l = st.session_state["scripts"]
    l[ind] = st.session_state[widget_key]
    replace_state("scripts", l)
    st.toast("Script updated!")

#! Session States--------------------------------------------------------------
def replace_state(state_name, var2replace):
    if state_name in st.session_state:
        del st.session_state[state_name]
    st.session_state[state_name] = var2replace

def extend_state(state_name, var2append):
    # Deep copy the session state
    session_state_copy = copy.deepcopy(st.session_state[state_name])
    del st.session_state[state_name]
    st.session_state[state_name] = session_state_copy + var2append

def extend_dictstate(state_name, var2append):
    # Deep copy the session state
    session_state_copy = copy.deepcopy(st.session_state[state_name])
    del st.session_state[state_name]
    st.session_state[state_name] = session_state_copy | var2append

def create_state(state_name, var2create):
    if state_name not in st.session_state:
        st.session_state[state_name] = var2create


def init_session_state():
    # For side bar:
    create_state('show_confirm_button', False)
    create_state("groq_key", "")
    create_state("eleven_key", "")
    create_state("serp_key", "")

    # For tab 1:
    create_state('topic', "")
    create_state('comments', "")
    create_state('delete_prev_runs', False)

    
    # For tab 2:
    create_state('queries', [])
    create_state('thumbnails_dict', False)
    create_state('jsons', {})
    create_state('thumbnails_selected', [])
    create_state('images_selected', [])
    create_state('img_dict', {})

    # For tab 3:
    #create_state('image_desc', [])
    create_state('duration', 5)
    create_state('include_title', True)
    create_state('include_index', True)
    create_state('include_title_sections', True)
    create_state('indices', [])
    create_state('descriptions', [])
    create_state('prs', None)

    # For tab 4:
    create_state('delete_pptx', False)
    create_state('script_comments', "")
    create_state('scripts', [])



def create_directories():
    directories = ['out', 'img', 'outvoices', 'outimages', 'config']
    for directory in directories:
        os.makedirs(directory, exist_ok=True)

def app():
    st.title("Slideo") #Slide + Video = Slideo
    init_session_state()
    create_directories()

    # Sidebar for API configuration
    with st.sidebar:
        sidebar()

    # Main content tabs
    tab1, tab2, tab3, tab4 = st.tabs(["Topic", "Images", "PPT Design", "Script & Video"])

    with tab1:
        #Topic and comments for the presentation
        st.header("Presentation Info")
        st.text_input("Enter the topic of your presentation:", key="topic_input", on_change=widget2state, args=["topic", "topic"])
        st.text_area("Enter any comments or suggestions for the presentation (optional):", key="comments_input", on_change=widget2state, args=["comments", "comments"])

        #Delete previous runs
        st.header("Utilities & Configuration")
        if st.button("Delete files from previous runs", key = "del_prev_runs"):
            replace_state('delete_prev_runs', True)
            st.error("Are you sure you want to all the files from previous runs?")
            st.toast("Warning: All files will be permanently deleted and cannot be recovered", icon="⚠️")
    
        if st.session_state['delete_prev_runs']:
            if st.button("Yes, proceed with delete.", key = "conf_del_prev_runs"):
                delete_previous_runs() 
                replace_state('delete_prev_runs', False)

                #Delete the buttons
                del st.session_state.del_prev_runs
                del st.session_state.conf_del_prev_runs

            


    # Tab 2: Images
    with tab2:
        col1, col2 = st.columns([3, 1])
        with col1:
            st.header("Add the queries")
        with col2:
            st.write("")
            st.write("")
            vis = st.checkbox("Show Section", value=True, key="Add the queries")
        
        if vis:
            col1, col2 = st.columns([2, 2])
            with col1:
                # Generate queries and get images
                num_queries = st.number_input("Number of LLM-generated queries:", min_value=0, max_value=10, value=4)
                if st.button("Generate Queries For the Topic"):
                    # Initialize OpenAI client
                    st.write(f"num_queries = {num_queries}")
                    try:
                        if st.session_state.topic != "":
                            client = OpenAI(base_url="https://api.groq.com/openai/v1", api_key=st.session_state["groq_key"])
                            groqmodel = "llama3-8b-8192"
                            queries_generated = LLM_queries(groqmodel, client, st.session_state.topic, st.session_state.comments, num_queries=num_queries)
                            extend_state('queries', queries_generated)
                            st.success("Added queries:\n" + "\n".join(queries_generated))
                        else:
                           st.error(f"Set a topic to suggest queries related.") 
                    except Exception as e:
                        st.error(f"Error saving generating the queries: {e}")
            with col2:
                # Manual query input
                manual_query = st.text_input("Or add your own search queries:")
                if st.button("Add Custom Query"):
                    if manual_query:
                        extend_state('queries', [manual_query])
                        st.success(f"Added query: {manual_query}")
                    else:
                        st.warning("Please enter a query first")
        
        col1, col2 = st.columns([3, 1])
        with col1:
            st.header("Choose the queries")
        with col2:
            st.write("")
            st.write("")
            vis = st.checkbox("Show Section", value=True, key="Choose the queries")
        if vis:
            chosen_queries = st.multiselect(
                                        "Choose the Google queries for searching images for the slides",
                                        st.session_state.queries,
                                        []
                                    )
            #replace_state("chosen_queries", chosen_queries) #! In case I need it to be a session state

            if st.button("Download Thumbnails"):
                
                if chosen_queries:
                    for query in chosen_queries:
                        try:
                            images = search(query, st.session_state["serp_key"])

                            #! Added a dictionary of all jsons
                            dict = {query : images}
                            extend_dictstate('jsons', dict)

                            paths_downloads = save_images(query, images, ref_names = [], num = 5, thumbnails = True, folder_dir = 'img') 
                        except Exception as e:
                            st.error(f"An error occurred: {e}")
                else: 
                    st.error("No queries were selected.")
            
        # Choosing the images:
        col1, col2 = st.columns([3, 1])
        with col1:
            st.header("Choose Images")
        with col2:
            st.write("")
            st.write("")
            vis = st.checkbox("Show Section", value=True, key="Choose Images")
        
        if vis:
            if st.button("Load thumbnails"):
                try:
                    with st.spinner("Loading thumbnails, please wait..."):
                        thumbnails_dict = get_thumbnails_dict()
                        replace_state("thumbnails_dict", thumbnails_dict)

                        jsons_dict = get_jsons_dict()
                        replace_state("jsons", jsons_dict)

                    st.toast("Ready!", icon = '🤯')
                except Exception as e:
                    st.error(f"An error occurred: {e}")
                
            #Load the images
            if st.session_state['thumbnails_dict']:
                clicked = [""] * len(st.session_state['thumbnails_dict'])
                for i, (query, paths_downloads) in enumerate(st.session_state['thumbnails_dict'].items()):
                    col1, col2 = st.columns([4, 1])
                    with col1:
                        st.subheader(query + ":")
                        clicked[i] = image_select("", paths_downloads, key = f"images_query{i}")
                    with col2:
                        num_queries = st.number_input("Number of extra images:", min_value=2, value=5, key = f"num_extra{i}")
                        if st.button("Get More Images For This Query", key = f"button_add_images_query{i}"):
                            msg = st.toast("Downloading the images...", icon = '🐢')
                            l = len(st.session_state.thumbnails_dict[query])
                            msg.toast("Done!", icon = '👍')
                            add_paths(query, st.session_state[f"num_extra{i}"])
                            
                            if len(st.session_state.thumbnails_dict[query]) > l:
                                msg.toast("Press the \"Load Thumbnails\" button at the begining of section \"Choose Images\" to see the new images", icon = '💡')
                                #st.success("Press the \"Load Thumbnails\" button at the begining of section \"Choose Images\" to see the new images")
                            else:
                                
                                msg.toast("No extra images were downloaded, an error occurred. If it was a problem with the links, try downloading a bigger number of extra images instead.", icon = '🔄')
                                #st.warning("No extra images were downloaded, there was an error with all the links. Try downloading a bigger number of extra images instead.")
                        if st.button("Use selected image", key = f"button_use_image_query{i}"):
                            path_selected = clicked[i]
                            extend_state('thumbnails_selected', [path_selected])
            else: 
                st.error("No thumbnails loaded.")

            st.write("### Selected Thumbnails:")
            if st.session_state.thumbnails_selected:
                for i, path in enumerate(st.session_state.thumbnails_selected, 1):
                    st.write(f"**Thumbnail {i}:** `{path.split("\\")[-1]}`")
            else:
                st.write("*No thumbnails selected yet*")

        col1, col2 = st.columns([3, 1])
        with col1:
            st.header("Download chosen images")
        with col2:
            st.write("")
            st.write("")
            vis = st.checkbox("Show Section", value=True, key="Download chosen images")
        
        if vis:
            if st.button("Download Full Resolution Selected Images"):
                with st.spinner("Downloading images, please wait..."):
                    #All images without the name thumbnail are deleted before downloading new images again:
                    delete_non_thumbnail_images(folder_dir='img')
                    replace_state("images_selected", [])

                    #Find in which query is the path that we are looking for.
                    for path in st.session_state.thumbnails_selected:
                        for query, paths in st.session_state.thumbnails_dict.items():
                            if path in paths:
                                actual_query = query
                                break
                        ref = path.split('thumbnail_')[-1]
                        paths = save_images(actual_query, ref_names = [ref], num = 1, thumbnails = False, folder_dir = 'img') 
                        extend_state("images_selected", paths)

                    st.write(st.session_state.images_selected)
                    st.toast("If an image does not appear, there might have been an issue with the download, see the terminal for more info", icon="💡")
                    client = OpenAI(base_url="https://api.groq.com/openai/v1", api_key=st.session_state["groq_key"])
                    img_dict = write_img_dict(st.session_state.images_selected, client)
                    replace_state('img_dict', img_dict)
                
            #Show all images with their image_desc
            if st.session_state.img_dict != {}:
                st.write("### Final Images and Descriptions:")
                for img_path, description in st.session_state.img_dict.items():
                    col1, col2 = st.columns([2, 1])
                    with col1:
                        st.image(img_path)
                    with col2:
                        st.text_area("Description", value=description, key=f"desc_{img_path}", on_change=modify, args=[img_path,f"desc_{img_path}"])
        





    # Tab 3: PPT Design
    with tab3:
        st.header("Layout")
        if not st.session_state.images_selected:
            st.warning("Images are an essential component of an engaging presentation. We strongly recommend to select images in the Images tab before proceeding with presentation creation.")
        
        duration = st.number_input("Enter desired presentation duration in minutes (approx.):", min_value=1, max_value=20, value=7)
        replace_state("duration", duration)
        include_title = st.checkbox("Include title slide?", value=True)
        replace_state("include_title", include_title)
        include_index = st.checkbox("Include index slide?", value=True)
        replace_state("include_index", include_index)
        include_title_sections = st.checkbox("Include title sections?", value=True)
        replace_state("include_title_sections", include_title_sections)

        #Layout building
        col1, col2, col3, _ = st.columns([2.5,1,3,5])
        with col1:
            if st.button("Build Layout"):
                msg = st.toast("Building the layout for the slides...", icon = '🛠️')
                try:
                    if st.session_state.topic == "":
                        msg.toast("Set a topic first in the Topic Tab!", icon = '💡')
                    else:
                        image_desc = list(st.session_state.img_dict.values())
                        client = OpenAI(base_url="https://api.groq.com/openai/v1", api_key=st.session_state["groq_key"])
                        groqmodel = "llama3-8b-8192"

                        indices, descriptions = build_layout_groq(client, groqmodel, st.session_state.topic, st.session_state.duration, st.session_state.comments, st.session_state.include_title, st.session_state.include_index, st.session_state.include_title_sections, image_desc)

                        replace_state("indices", indices)
                        replace_state("descriptions", descriptions)

                        print("Saving the indices and descriptions of the layout to out/descriptions.txt")
                        save_layout_prompt(st.session_state.indices, st.session_state.descriptions)

                        msg.toast(f"Done!", icon = '🚀')

                except Exception as e:
                    msg.toast(f"An error occurred!\n{e}", icon = '🤔')
        
        with col2:
            st.write("")
            st.write("or")


        with col3:
            #Load indices and descriptions if any
            if st.button("Load Layout from File"):
                if os.path.exists("out/descriptions.txt"):
                    indices, descriptions = get_layout_prompt(file_path='out/descriptions.txt')
                    replace_state("indices", indices)
                    replace_state("descriptions", descriptions)
                    st.toast("Successfully loaded descriptions and indices!", icon= '👌')
                else:
                    st.toast("There is no file to load the layout from!", icon= '💥')
            

        if st.session_state.descriptions != [] and st.session_state.indices != []:
            st.info("Remember to press Ctrl+Enter to save the changes on each description block! When changes are correctly saved a message saying \"Description updated!\" will pop up.")
            if st.session_state.img_dict != {}:
                st.write("Image integration is supported in two slide types: 'Single Image' and 'Multiple Images' (2-4 images). To include an image in a certain slide, they must be referenced in the slide description using the following format:")
                for image in st.session_state.img_dict.values():
                    _, col = st.columns([1,8])
                    with col:
                        st.write(f"{image}")
                
            index_meaning ={
                    0 : "Title",
                    2 : "Section Title",
                    1 : "Content (bullet points)",
                    4 : "Content (comparison in 2 columns)",
                    8 : "Single image",
                    5 : "Multiple images",
                    11 : "Index"
                }
            reverse_dict = {v: k for k, v in index_meaning.items()}#Since it is bijective this is ok
            options_list = list(index_meaning.values())
            # options_list = [  "Title",
            #                 "Section Title",
            #                 "Content (bullet points)",
            #                 "Content (comparison in 2 columns)",
            #                 "1 image",
            #                 "Multiple images",
            #                 "Index"
            #              ]
        
            col1, col2 = st.columns([1, 4])
            with col1:
                st.subheader("Slide type")
            with col2:
                st.subheader("Description of the slide")
        
            for i, (index, desc) in enumerate(zip(st.session_state.indices, st.session_state.descriptions)):
                st.divider()

                _, col, _ = st.columns([2, 1, 2])
                with col:
                    st.button("Add slide here", key = f"add_desc_{i}", on_click=add_desc_ind, args=[i])
                
                st.divider()

                col1, col2, col3 = st.columns([2, 5, 1])
                with col1:
                    st.selectbox(
                                        f"Choose slide {i+1} type",
                                        options_list,
                                        index = options_list.index(index_meaning[index]),
                                        key = f"ind_input_{i}",
                                        on_change=edit_ind, 
                                        args=[f"ind_input_{i}", reverse_dict, i]
                                    )
                with col2:
                    st.text_area(f"Description slide {i+1}", desc, key = f"desc_input_{i}", on_change=edit_desc, args=[f"desc_input_{i}", i])
                with col3: 
                    st.button('❌', key = f"remove_desc_{i}", on_click=remove_desc_ind, args=[i])
                
            st.divider()

            _, col, _ = st.columns([2, 1, 2])
            with col:
                st.button("Add slide here", key = f"add_desc_{len(st.session_state.indices)}", on_click=add_desc_ind, args=[len(st.session_state.indices)])
            
            st.divider()

            if st.button("Save Descriptions to a file"):
                try:
                    save_layout_prompt(st.session_state.indices, st.session_state.descriptions)
                    st.toast("Successfully saved descriptions and indices!", icon= '👌')
                except Exception as e:
                    st.toast(f"Error saving descriptions: {e}", icon='❌')
                
        
        st.header("Presentation Design")
        if st.button("Build the presentation"):
            msg = st.toast("Finding which slides contain which images...")
            images = find_img_in_slides(st.session_state.img_dict, st.session_state.descriptions) #get which images are in which slides

            # with open("out/img_dict.json", "w") as img_dict_file:
            #     json.dump(st.session_state.img_dict, img_dict_file)
            
            # with open("out/images_in_slides.json", "w") as images_file:
            #     json.dump(images, images_file)
            msg.toast("Creating a presentation with the images and the layout...")
            prs = build_presentation(st.session_state.indices, images) #Create the ppt with the images
            msg.toast("Adding text to the slides according to their descriptions...")

            client = OpenAI(
                base_url="https://api.groq.com/openai/v1",
                api_key=st.session_state.groq_key
            )
            prs = add_content(prs, client, st.session_state.indices, st.session_state.descriptions) #Addind the text to the images
            prs.save("out/output.pptx")
            replace_state('prs', prs)
            msg.toast("Done! Presentation ready to be downloaded", icon= '👌')
        
        if not os.path.exists("out/output.pptx"):
            st.download_button(label = "Download Presentation", data = "",help ="There is no PowerPoint generated that can be downloaded", disabled=True)
        else:
            with open("out/output.pptx", "rb") as file:
                st.download_button(
                    label="Download Presentation",
                    data=file,
                    file_name="Slideo.pptx"
                )
        




    # Tab 4: Script & Video
    with tab4:
        #Delete the uploaded pptx to be able to upload another one
        if os.path.exists("out/output.pptx"):
            if st.button("Delete stored pptx", key="del_pptx"):
                replace_state('delete_pptx', True)
                st.error("Are you sure you want to delete the stored pptx?")
                st.toast("Warning: The pptx file will be lost if not downloaded. Download it in the PPT Design tab.", icon="⚠️")
            
        if st.session_state['delete_pptx']:
            if st.button("Yes, proceed with delete.", key = "conf_del_pptx"):
                os.remove("out/output.pptx")
                st.toast("Deleted the existing presentation file.", icon='👌')
                replace_state('delete_pptx', False)
                del st.session_state.del_pptx
                del st.session_state.conf_del_pptx

        

        #Upload a pptx
        if not os.path.exists("out/output.pptx"):
            #Load the script             
            uploaded_file = st.file_uploader("Upload an existing presentation", key= "file_upload", type="pptx")
            if uploaded_file is not None:
                # To read file as bytes:
                bytes_data = uploaded_file.getvalue()
                # Save uploaded presentation to file
                with open("out/output.pptx", "wb") as f:
                    f.write(bytes_data)
                # Load the presentation into session state
                prs = Presentation("out/output.pptx")
                replace_state('prs', prs)
                st.toast("Successfully loaded the presentation!", icon= '👌')
                #Remove the file uploader
                del st.session_state.file_upload
            else:
                st.warning("Please create the presentation first in the PPT Design tab or upload one.")
            
        #This if statement cannot be an else of the previous if block due to how streamlit loads the reloads the page
        if os.path.exists("out/output.pptx"):
            #! Delete uploaded pptx button to be able to upload a new one
            st.info("Please make any necessary modifications to the slides prior to generating the script, ensuring that it reflects the final version of your presentation.")
            #Create a script
            st.header("Script")
            script_comments = st.text_area("Pass a note to the scripter with any requirements or suggestions:", key="sccom_input", on_change=widget2state, args=["script_comments", "sccom"])
            if st.button("Create Script"):
                msg = st.toast("Writing the script for each slide...", icon = '🛠️')
                with st.spinner("Writing script, please wait..."):
                    client = OpenAI(
                        base_url="https://api.groq.com/openai/v1",
                        api_key=st.session_state.groq_key
                    )
                    scripts = scripter("out/output.pptx", script_comments, client)
                    replace_state("scripts", scripts)
                    # Only manually save the script
                    # with open("out/script.txt", "w") as f:
                    #     for i, script in enumerate(st.session_state.scripts):
                    #         f.write(f"Slide {i+1}:\n{script}\n\n")
                    # msg.toast("Script saved to out/script.txt", icon= '👌')
                    msg.toast("Done!", icon= '👌')

            if st.button("Load Scripts from file"):
                if os.path.exists("out/script.txt"):
                    scripts = get_scripts("out/script.txt")
                    replace_state("scripts", scripts)
                    st.toast("Successfully loaded scripts!", icon='👌')
                else:
                    st.toast("There is no script file to load from.", icon='💥')
            
            # Edit the script
            if st.session_state.scripts != []:
                st.subheader("Edit the scripts:")
                st.info("Remember to press Ctrl+Enter to save the changes on each block of the script! When changes are correctly saved a message saying \"Script updated!\" will pop up.")
                for i, script in enumerate(st.session_state.scripts):                
                    st.divider()

                    st.text_area(f"Script slide {i+1}", script, key = f"script_input_{i}", on_change=edit_script, args=[f"script_input_{i}", i])
                    
                st.divider()


                if st.button("Save Scripts to a file"):
                    try:
                        with open("out/script.txt", "w") as f:
                            for i, script in enumerate(st.session_state.scripts):
                                f.write(f"Slide {i+1}:\n{script}\n\n")
                        st.toast("Successfully saved scripts!", icon= '👌')
                    except Exception as e:
                        st.toast(f"Error saving descriptions: {e}", icon='❌')

            st.header("Video")

            if st.session_state.scripts == [] or not os.path.exists("out/output.pptx"):
                #Ask for the data needed to create the video
                st.warning("Both a PowerPoint presentation and a script are required to create a video. Please ensure you have generated or loaded both before proceeding.")
                st.button("Create the video", disabled=True)
            else:
                #Create the video
                if st.button("Create the video"):
                    #Create the audio files
                    voice_id = "29vD33N1CtxCmqQRPOHJ"
                    msg = st.toast("Starting text-to-speech pipeline...")
                    bar = st.progress(0, "Voice generation")
                    for i, script in enumerate(st.session_state.scripts):
                        bar.progress(i/len(st.session_state.scripts), f"Voice generation: Slide {i+1}...")
                        filename = f"Slide{i+1}"
                        if not os.path.exists(f"outvoices/{filename}.mp3"):
                            try:
                                ok = text_to_speech(script, st.session_state.eleven_key, voice_id, f"outvoices/{filename}")
                            except Exception as e:
                                # Ensure the raised object is a byte string and decode it
                                if isinstance(e, bytes):
                                    error_str = e.decode("utf-8")  # Decode bytes to string
                                    error_data = json.loads(error_str)  # Parse string to JSON
                                    detail = error_data.get("detail", {})
                                    status = detail.get("status", "unknown_error")
                                    message = detail.get("message", "No message provided")
                                    msg.toast(f"Error generating audio for slide {i+1}: \n{status} - {message}", icon= '💥')
                                else:
                                    msg.toast(f"Unexpected exception: {e}", icon= '💥')
                                break
                        else:
                            bar.progress(i/len(st.session_state.scripts), f"Found existing voice for Slide {i+1}...")
                            time.sleep(0.2)
                    bar.empty()
                    #Create the images
                    msg.toast("Converting all slides into images for the video...")
                    try:
                        PPTconvert("out/output.pptx", "outimages", formatType=18)
                    except Exception as e:
                        st.error(f"Error converting PPT to images: {e}")
                    msg.toast("The video might take a few minutes, depending on the length of of the video and the hardware. Please be patient")
                    #Merge the images and audio into a video
                    with st.spinner('Creating the video...'):
                        create_simple_video(
                            slide_folder='outimages',
                            audio_folder='outvoices',
                            output_video='out/output_video.mp4',
                            silent_duration=5.0,
                            transition_duration=0.5
                            )
            
            
            # Create a download button for the video
            if os.path.exists('out/output_video.mp4'):
                with open('out/output_video.mp4', 'rb') as video_file:
                    st.download_button(
                        label="Download Video",
                        data=video_file,
                        file_name="Slideo.mp4"
                    )
            else: 
                st.download_button(label = "Download Video", data = "", help = "There is no video generated that can be downloaded", disabled=True)
            
            

if __name__ == "__main__":
    app()