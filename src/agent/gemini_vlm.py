from google import genai
from dotenv import load_dotenv
load_dotenv()
from google.genai import types
import time
client = genai.Client()
import requests

video_url = "https://pub-b215a097b7b243dc86da838a88d50339.r2.dev/media/videos/PythagoreanTheorem/480p15/PythagoreanTheorem.mp4"

response = requests.get(video_url)
response.raise_for_status()

video_bytes = response.content

client = genai.Client()
response = client.models.generate_content(
    model='models/gemini-2.5-flash',
    contents=types.Content(
        parts=[
            types.Part(
                inline_data=types.Blob(data=video_bytes, mime_type='video/mp4')
            ),
            types.Part(text='look at the video and find the errors in visuals, such as overlapping, inconsistency of video with the explanation, inconsistency in video and audio mistmatching')
        ]
    )
)
print(response.text)