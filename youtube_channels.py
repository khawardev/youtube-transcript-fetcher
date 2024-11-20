from googleapiclient.discovery import build
from youtube_transcript_api import YouTubeTranscriptApi
import logging

API_KEY = 'AIzaSyAMmJwm780uNHbVS60CmwbO-SbpC8ZaT2s'

def fetch_channel_data(channel_url):
    def extract_channel_id(channel_url):
        if 'channel/' in channel_url:
            return channel_url.split('channel/')[1].split('/')[0]
        return None

    channel_id = extract_channel_id(channel_url)
    if not channel_id:
        return None

    youtube = build('youtube', 'v3', developerKey=API_KEY)

    try:
        channel_response = youtube.channels().list(part='snippet', id=channel_id).execute()
        channel_info = channel_response['items'][0]['snippet']

        video_response = youtube.search().list(part='snippet', channelId=channel_id, maxResults=5, order='date').execute()
        for video in video_response['items']:
            video_id = video['id']['videoId']
            transcript_text = ""
            try:
                transcript = YouTubeTranscriptApi.get_transcript(video_id)
                transcript_text = ' '.join([entry['text'] for entry in transcript])[:50000]
            except Exception as e:
                transcript_text = f"Error: {e}"
            return {
                'SP_Channel_URL': channel_url,
                'SP_Channel_Title': channel_info['title'],
                'SP_Latest_Video_Title': video['snippet']['title'],
                'SP_Video_URL': f"https://www.youtube.com/watch?v={video_id}",
                'SP_Video_Transcript': transcript_text
            }
    except Exception as e:
        logging.error(f"Error fetching channel data: {e}")
        return None
