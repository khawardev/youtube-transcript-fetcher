from googleapiclient.discovery import build
from youtube_transcript_api import YouTubeTranscriptApi
import logging

API_KEY = 'AIzaSyAMmJwm780uNHbVS60CmwbO-SbpC8ZaT2s'

def fetch_playlist_data(playlist_url):
    def extract_playlist_id(playlist_url):
        if 'playlist?list=' in playlist_url:
            return playlist_url.split('playlist?list=')[1]
        return None

    playlist_id = extract_playlist_id(playlist_url)
    if not playlist_id:
        return None

    youtube = build('youtube', 'v3', developerKey=API_KEY)

    try:
        video_response = youtube.playlistItems().list(part='snippet', playlistId=playlist_id, maxResults=1).execute()
        latest_video = video_response['items'][0]
        video_id = latest_video['snippet']['resourceId']['videoId']

        transcript_text = ""
        try:
            transcript = YouTubeTranscriptApi.get_transcript(video_id)
            transcript_text = ' '.join([entry['text'] for entry in transcript])[:50000]
        except Exception as e:
            transcript_text = f"Error: {e}"

        return {
            'SP_Playlist_URL': playlist_url,
            'SP_Latest_Video_Title': latest_video['snippet']['title'],
            'SP_Video_URL': f"https://www.youtube.com/watch?v={video_id}",
            'SP_Video_Transcript': transcript_text
        }
    except Exception as e:
        logging.error(f"Error fetching playlist data: {e}")
        return None
