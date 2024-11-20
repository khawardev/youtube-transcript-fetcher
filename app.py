import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from youtube_channels import fetch_channel_data
from youtube_playlists import fetch_playlist_data
import sys
import platform
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
with st.sidebar:
    st.header("Actions")
    if st.button("🔄 Get Transcripts from Channels and Update Worksheet"):
        with st.spinner("Fetching channel data..."):
            urls = df_channels[df_channels['SP_Latest_Video_Title'].isnull()]['SP_Channel_URL'].tolist()
            processed_channel_data = []

            for url in urls:
                data = fetch_channel_data(url)
                if data:
                    processed_channel_data.append(data)

            if processed_channel_data:
                updated_channel_data = pd.DataFrame(processed_channel_data)
                merged_data = pd.merge(df_channels, updated_channel_data, on='SP_Channel_URL', how='left', suffixes=('', '_new'))
                
                for column in updated_channel_data.columns:
                    if column != 'SP_Channel_URL':
                        merged_data[column].update(merged_data[f"{column}_new"])
                        merged_data.drop(columns=[f"{column}_new"], inplace=True)

                try:
                    conn.update(worksheet="yt_channels", data=merged_data)
                    st.balloons()
                    st.success("Channels Worksheet Updated Successfully! 🤓")
                except Exception as e:
                    st.error(f"Error updating worksheet: {e}")
            else:
                st.warning("No channel data was fetched to update.")

    if st.button("🔄 Get Transcripts from Playlists and Update Worksheet"):
        with st.spinner("Fetching playlist data..."):
            urls = df_playlists[df_playlists['SP_Latest_Video_Title'].isnull()]['SP_Playlist_URL'].tolist()
            processed_playlist_data = []

            for url in urls:
                data = fetch_playlist_data(url)
                if data:
                    processed_playlist_data.append(data)

            if processed_playlist_data:
                updated_playlist_data = pd.DataFrame(processed_playlist_data)
                merged_data = pd.merge(df_playlists, updated_playlist_data, on='SP_Playlist_URL', how='left', suffixes=('', '_new'))
                
                for column in updated_playlist_data.columns:
                    if column != 'SP_Playlist_URL':
                        merged_data[column].update(merged_data[f"{column}_new"])
                        merged_data.drop(columns=[f"{column}_new"], inplace=True)

                try:
                    conn.update(worksheet="yt_playlists", data=merged_data)
                    st.balloons()
                    st.success("Playlists Worksheet Updated Successfully! 🤓")
                except Exception as e:
                    st.error(f"Error updating worksheet: {e}")
            else:
                st.warning("No playlist data was fetched to update.")

    st.markdown("---")
    st.info("ℹ️ Tip: Click a button to fetch or update data.")
