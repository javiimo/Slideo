import requests

def text_to_speech(text, api_key, voice_id, output_name='output'):
    CHUNK_SIZE = 1024
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"

    headers = {
        "Accept": "audio/mpeg",
        "Content-Type": "application/json",
        "xi-api-key": api_key
    }

    data = {
        "text": text,
        "model_id": "eleven_multilingual_v2",
        "voice_settings": {
            "stability": 0.8,
            "similarity_boost": 0.5
        }
    }

    response = requests.post(url, json=data, headers=headers)
    if response.ok:
        with open(output_name + ".mp3", 'wb') as f:
            for chunk in response.iter_content(chunk_size=CHUNK_SIZE):
                if chunk:
                    f.write(chunk)
    else:
        raise Exception(response.content)
    return response.ok



if __name__ == "__main__":  
    ELEVENLABS_API_KEY = open('cred/apikeys.txt').readlines()[1].strip()
    text = "Hello, this is a test of the text to speech system."
    voice_id = "wTOf7ACatDj2mwMoHZ97"  # Nichalia Schwartz's voice is not working
    # voice_id = "wTOf7ACatDj2mwMoHZ97" # Not working neither
    voice_id = "29vD33N1CtxCmqQRPOHJ"
    try: 
        response = text_to_speech(text, ELEVENLABS_API_KEY, voice_id, "test_output2")
    except Exception as e:
        print(e)
    #print(f"API Response Status: {status}")
    print("Response Attributes:")
    attributes = [
        'apparent_encoding', 'close', 'connection', 'content', 'cookies', 
        'elapsed', 'encoding', 'headers', 'history', 'is_permanent_redirect', 
        'is_redirect', 'iter_content', 'iter_lines', 'json', 'links', 
        'next', 'ok', 'raw', 'reason', 'request', 
        'status_code', 'url'
    ]
    
    for attr in attributes:
        print(f"{attr}: {getattr(response, attr)}")

