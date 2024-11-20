import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from youtube_channels import fetch_channel_data
from youtube_playlists import fetch_playlist_data
import asyncio
import logging

# Initialize logger
logging.basicConfig(filename="app.log", level=logging.INFO, format="%(asctime)s - %(message)s")

# Initialize session state for YouTube data
if 'updated_youtube_data' not in st.session_state:
    st.session_state.updated_youtube_data = None

# Set a more engaging and descriptive title
st.title("📺 YouTube Transcripts Fetcher")

st.markdown("""
Welcome to the YouTube Transcripts Fetcher! 📄 This app allows you to fetch and update YouTube channel and playlist transcripts effortlessly. 
Below, you can see previews of your data and use the sidebar to trigger updates.
""")

# Establishing a Google Sheets connection
conn = st.connection("gsheets", type=GSheetsConnection)

# Display channel data preview
st.subheader("📊 Channel Data")
df_channels = conn.read(worksheet="yt_channels")
st.dataframe(df_channels)

# Display playlist data preview
st.subheader("📊 Playlist Data")
df_playlists = conn.read(worksheet="yt_playlists")
st.dataframe(df_playlists)

# Sidebar buttons for updating data
async def update_data(dataframe, fetch_function, key_column, worksheet_name):
    urls = dataframe[dataframe['SP_Latest_Video_Title'].isnull()][key_column].tolist()
    results = []

    for url in urls:
        try:
            result = fetch_function(url)
            if result:
                results.append(result)
        except Exception as e:
            logging.error(f"Error processing {url}: {e}")

    if results:
        new_data = pd.DataFrame(results)
        merged_data = pd.merge(dataframe, new_data, on=key_column, how='left', suffixes=('', '_new'))
        
        for column in new_data.columns:
            if column != key_column:
                # Use loc to avoid chained assignment warning
                merged_data.loc[:, column] = merged_data[f"{column}_new"]
                merged_data.drop(columns=[f"{column}_new"], inplace=True)

        try:
            conn.update(worksheet=worksheet_name, data=merged_data)
            st.success(f"{worksheet_name} Worksheet Updated Successfully!")
            st.balloons()
        except Exception as e:
            st.error(f"Error updating {worksheet_name}: {e}")
    else:
        st.warning(f"No data fetched for {worksheet_name}.")

with st.sidebar:
    st.header("Actions")
    if st.button("🔄 Get Transcripts from Channels and Update Worksheet"):
        asyncio.run(update_data(df_channels, fetch_channel_data, 'SP_Channel_URL', 'yt_channels'))

    if st.button("🔄 Get Transcripts from Playlists and Update Worksheet"):
        asyncio.run(update_data(df_playlists, fetch_playlist_data, 'SP_Playlist_URL', 'yt_playlists'))

    st.markdown("---")
    st.info("ℹ️ Tip: Click a button to fetch or update data.")

# Fetch channel data function
from googleapiclient.discovery import build
from youtube_transcript_api import YouTubeTranscriptApi

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

# Fetch playlist data function
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