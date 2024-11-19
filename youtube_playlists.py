from googleapiclient.discovery import build
from youtube_transcript_api import YouTubeTranscriptApi
import os
from dotenv import load_dotenv
load_dotenv()

# Function to extract playlist ID from URL
def extract_playlist_id(playlist_url):
    if 'playlist?list=' in playlist_url:
        return playlist_url.split('playlist?list=')[1]
    return None

# Function to fetch playlist data and the latest video details
def fetch_playlist_data(playlist_url):
    playlist_id = extract_playlist_id(playlist_url)
    if not playlist_id:
        return None
    
    youtube = build('youtube', 'v3', developerKey=os.getenv('YOUTUBE_SECRET'))
    
    # Get videos in the playlist
    video_response = youtube.playlistItems().list(
        part='snippet',
        playlistId=playlist_id,
        maxResults=1
    ).execute()
    
    if not video_response['items']:
        return None
    
    latest_video = video_response['items'][0]
    video_id = latest_video['snippet']['resourceId']['videoId']
    video_title = latest_video['snippet']['title']
    video_url = f"https://www.youtube.com/watch?v={video_id}"
    transcript_text = ""
    
    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id)
        transcript_text = ' '.join([entry['text'] for entry in transcript])
    except Exception as e:
        transcript_text = f"Error fetching transcript: {e}"
    
    return {
        'SP_Playlist_URL': playlist_url,
        'SP_Latest_Video_Title': video_title,
        'SP_Video_URL': video_url,
        'SP_Video_Transcript': transcript_text[:49990]
    }
