import comtypes
import comtypes.client
import os
import moviepy

def PPTconvert(inputFileName, outputFileName, formatType=18):
    # Format type 32 is save as pdf
    # Format type 18 is save as PNG

    # Convert relative path to absolute path
    abs_input_path = os.path.abspath(inputFileName)
    abs_output_path = os.path.abspath(outputFileName)

    # Ensure input file exists
    if not os.path.exists(abs_input_path):
        raise FileNotFoundError(f"Input file not found: {abs_input_path}")

    # Initialize the COM library
    comtypes.CoInitialize()

    try:
        powerpoint = comtypes.client.CreateObject("Powerpoint.Application")
        powerpoint.Visible = 1

        # Append .PNG if not exporting to pdf
        if not outputFileName.lower().endswith('pdf'):
            abs_output_path = abs_output_path + ".PNG"
        
        try:
            deck = powerpoint.Presentations.Open(abs_input_path)
            deck.SaveAs(abs_output_path, formatType)  # formatType = 32 for ppt to pdf
            deck.Close()
        finally:
            powerpoint.Quit()
    finally:
        # Uninitialize the COM library
        comtypes.CoUninitialize()


import os
from moviepy.editor import ImageClip, AudioFileClip, concatenate_videoclips
from moviepy.video.fx.fadeout import fadeout
from moviepy.video.fx.fadein import fadein
from glob import glob

def create_simple_video(
    slide_folder='outimages',
    audio_folder='outvoices',
    output_video='out/output_video.mp4',
    silent_duration=3.0,
    transition_duration=0.5
):
    """
    Create a video from slides and audio files, gracefully handling missing files.
    
    Args:
        slide_folder (str): Path to folder containing slides
        audio_folder (str): Path to folder containing audio files
        output_video (str): Path for the output video
        silent_duration (float): Duration for slides without audio
        transition_duration (float): Duration of fade transitions
    """
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_video), exist_ok=True)
    
    # Get list of all slides and sort them
    slides = sorted(glob(os.path.join(slide_folder, 'Slide*.PNG')), 
               key=lambda x: int(''.join(c for c in x if c.isdigit())))
    total_slides = len(slides)
    
    if total_slides == 0:
        raise Exception(f"No slides found in {slide_folder}")
        
    print(f"Found {total_slides} slides to process")
    clips = []
    processed_slides = 0
    
    # Process each slide
    for slide_path in slides:
        # Extract slide number from filename
        slide_name = os.path.basename(slide_path)
        slide_num = slide_name.replace('Slide', '').replace('.PNG', '')
        audio_path = os.path.join(audio_folder, f'Slide{slide_num}.mp3')
        
        try:
            # Create slide clip
            slide_clip = ImageClip(slide_path)
            
            # Try to add audio if it exists
            duration = silent_duration
            if os.path.exists(audio_path):
                try:
                    audio_clip = AudioFileClip(audio_path)
                    slide_clip = slide_clip.set_audio(audio_clip)
                    duration = audio_clip.duration
                    print(f"Processed slide {slide_num} with audio (duration: {duration:.2f}s)")
                except Exception as e:
                    print(f"Note: Could not process audio for slide {slide_num}, using silent duration: {str(e)}")
            else:
                print(f"Processed slide {slide_num} without audio (duration: {duration:.2f}s)")
            
            # Set duration and add transitions
            slide_clip = slide_clip.set_duration(duration)
            
            # Add fade transitions
            if processed_slides > 0:  # Add fade in for all except the first slide
                slide_clip = fadein(slide_clip, transition_duration)
            if processed_slides < total_slides - 1:  # Add fade out for all except the last slide
                slide_clip = fadeout(slide_clip, transition_duration)
            
            clips.append(slide_clip)
            processed_slides += 1
            
        except Exception as e:
            print(f"Warning: Error processing slide {slide_num}, skipping: {str(e)}")
            continue
    
    if not clips:
        raise Exception("No slides were successfully processed")
    
    # Create final video
    print(f"\nCreating final video with {processed_slides} slides...")
    final_video = concatenate_videoclips(clips, method="compose")
    final_video.write_videofile(
        output_video,
        fps=24,
        codec='libx264',
        audio_codec='aac',
        threads=4,
        preset='medium'
    )
    print(f"\nVideo successfully created at: {output_video}")
    print(f"Total slides processed: {processed_slides} out of {total_slides}")

# Example usage:
# create_simple_video(
#     slide_folder='outimages',
#     audio_folder='outvoices',
#     output_video='out/output_video.mp4',
#     silent_duration=3.0,
#     transition_duration=0.5
# )




if __name__ == "__main__":
    #Get the images of each slide of the presentation
    # file_name = "out/out.pptx"
    # PPTconvert(file_name, "outimages", formatType=18)  # Changed to PNG format

    #Get a simple video
    create_simple_video(
        slide_folder='outimages',
        audio_folder='outvoices',
        output_video='out/output_video.mp4',
        silent_duration=5.0,
        transition_duration=0.5
        )