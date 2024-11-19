from googleapiclient.discovery import build
from youtube_transcript_api import YouTubeTranscriptApi
import os
from dotenv import load_dotenv
load_dotenv()

# Function to extract channel ID from URL
def extract_channel_id(channel_url):
    if 'channel/' in channel_url:
        return channel_url.split('channel/')[1].split('/')[0]
    elif '@' in channel_url:
        username = channel_url.split('@')[1].split('/')[0]
        return get_channel_id_from_username(username)
    return None

# Function to get channel ID from username
def get_channel_id_from_username(username):
    youtube = build('youtube', 'v3', developerKey='AIzaSyAMmJwm780uNHbVS60CmwbO-SbpC8ZaT2s')
    search_response = youtube.search().list(
        part='snippet',
        q=username,
        type='channel',
        maxResults=1
    ).execute()
    
    if 'items' in search_response and search_response['items']:
        return search_response['items'][0]['snippet']['channelId']
    return None

# Function to fetch channel info and latest video details
def fetch_channel_data(channel_url):
    channel_id = extract_channel_id(channel_url)
    if not channel_id:
        return None
    
    youtube = build('youtube', 'v3', developerKey='AIzaSyAMmJwm780uNHbVS60CmwbO-SbpC8ZaT2s')
    
    # Get channel details
    channel_response = youtube.channels().list(part='snippet', id=channel_id).execute()
    if not channel_response['items']:
        return None
    
    channel_info = channel_response['items'][0]['snippet']
    
    # Get latest video details
    video_response = youtube.search().list(
        part='snippet', channelId=channel_id, maxResults=5, order='date'
    ).execute()
    
    if not video_response['items']:
        return None
    
    # Check if the latest video is long-form (not a short)
    for video in video_response['items']:
        video_id = video['id'].get('videoId', None)
        video_title = video['snippet']['title']
        
        # Fetch video details to check duration
        video_details = youtube.videos().list(part='contentDetails', id=video_id).execute()
        if video_details['items']:
            duration = video_details['items'][0]['contentDetails']['duration']
            
            # YouTube duration format is in ISO 8601 (e.g., PT1H2M3S for 1 hour, 2 minutes, 3 seconds)
            # Checking if duration is greater than 1 minute (not a short)
            if 'M' in duration:  # Simple check for minute duration
                transcript_text = ""
                try:
                    transcript = YouTubeTranscriptApi.get_transcript(video_id)
                    transcript_text = ' '.join([entry['text'] for entry in transcript])
                except Exception as e:
                    transcript_text = f"Error fetching transcript: {e}"
                
                return {
                    'SP_Channel_URL': channel_url,
                    'SP_Channel_Title': channel_info['title'],
                    'SP_Latest_Video_Title': video_title,
                    'SP_Video_URL': f"https://www.youtube.com/watch?v={video_id}",
                    'SP_Video_Transcript': transcript_text[:50000]
                }
    
    return None
