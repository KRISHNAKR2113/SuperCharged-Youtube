import streamlit as st
import requests
import isodate

# Initialize session state for watched videos, watch later list, and points
if "watched" not in st.session_state:
    st.session_state.watched = []  # List to store watched video dictionaries
if "watch_later" not in st.session_state:
    st.session_state.watch_later = []  # List to store "Watch Later" video dictionaries
if "points" not in st.session_state:
    st.session_state.points = 0
if "last_query" not in st.session_state:
    st.session_state.last_query = ""

# ============ CONFIGURATION ============
API_KEY = "AIzaSyAMQLE3TZCiSBtyLOzZI5cnzslEf9YDEMc"  # Replace with your YouTube Data API key
MAX_RESULTS = 21  # Number of videos to fetch per query

st.set_page_config(page_title="📺Supercharged Youtube Premium Search📺", layout="wide")

# Inject CSS for dynamic gradient background, 3D hover on titles, and 16:9 video container
st.markdown(
    """
    <style>
    body {
        background: linear-gradient(270deg, #1e3c72, #2a5298, #1e3c72);
        background-size: 600% 600%;
        animation: Gradient 15s ease infinite;
        color: #ffffff;
    }
    @keyframes Gradient {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }
    [data-testid="stHeader"], [data-testid="stSidebar"] {
        background-color: #1f1f1f !important;
    }
    h1, h2, h3, h4, h5, h6 {
        color: #ffffff !important;
    }
    /* 3D hover effect on video titles */
    .video-title {
        transition: transform 0.3s ease;
    }
    .video-title:hover {
        transform: perspective(500px) rotateX(10deg) rotateY(10deg);
    }
    /* 16:9 video container styling */
    .video-container {
        position: relative;
        width: 100%;
        padding-bottom: 56.25%;
        height: 0;
    }
    .video-container iframe {
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
    }
    </style>
    """,
    unsafe_allow_html=True
)

st.title("🎬 Supercharged Youtube 🎬")

# Sidebar Navigation & Points System Info
st.sidebar.header("📺 Supercharged Youtube")
# Added "Watch Later" to the sidebar navigation
page = st.sidebar.radio("Go to", ["Home", "Trending", "History", "Watch Later"])
st.sidebar.header("🏆 Points System")
st.sidebar.write("10 points per search")
st.sidebar.write("20 points per video watched")
st.sidebar.write(f"🎯**Total Points:** {st.session_state.points}")

# Home page: Search & Length Filter (language option removed)
if page == "Home":
    col_search, col_length = st.columns([3, 1], gap="small")
    with col_search:
        query = st.text_input("🔎 Search for videos", "")
    with col_length:
        length_filter = st.selectbox("Filter by length", ["All", "Short (<5 min)", "Medium (5-15 min)", "Long (>15 min)"])
    search_clicked = st.button("Search")
else:
    query = ""
    length_filter = "All"
    search_clicked = False

# Trending page: Region selection (using mapping for proper region codes)
if page == "Trending":
    region_display = st.selectbox("Choose Language/Region", ["All", "US (English)", "ES (Spanish)", "IN (Hindi)"])
    region_code_map = {"US (English)": "US", "ES (Spanish)": "ES", "IN (Hindi)": "IN"}
    chosen_region = region_code_map.get(region_display, None)
else:
    region = None
    chosen_region = None

# ============ HELPER FUNCTIONS ============
def parse_duration(iso_duration: str) -> float:
    try:
        duration = isodate.parse_duration(iso_duration)
        return duration.total_seconds() / 60.0
    except Exception:
        return 0.0

def in_length_range(length_in_minutes: float, filter_option: str) -> bool:
    if filter_option == "All":
        return True
    elif filter_option == "Short (<5 min)":
        return length_in_minutes < 5
    elif filter_option == "Medium (5-15 min)":
        return 5 <= length_in_minutes <= 15
    else:
        return length_in_minutes > 15

def clamp(value, min_val, max_val):
    return max(min_val, min(value, max_val))

def calculate_rating(views: int, comments: int, length_min: float) -> float:
    rating_raw = (views / 5000.0) + (comments / 50.0) - (length_min / 2.0)
    return clamp(rating_raw, 0, 100)

def fetch_trending_videos(region_code=None):
    url = "https://www.googleapis.com/youtube/v3/videos"
    params = {
        "part": "snippet,statistics,contentDetails",
        "chart": "mostPopular",
        "maxResults": MAX_RESULTS,
        "key": API_KEY
    }
    if region_code and region_code != "All":
        params["regionCode"] = region_code
    resp = requests.get(url, params=params)
    if resp.status_code == 200:
        return resp.json().get("items", [])
    else:
        st.error("⚠️ Error fetching trending videos from YouTube.")
        return []

def fetch_search_results(search_query: str):
    if not search_query:
        return []
    url = "https://www.googleapis.com/youtube/v3/search"
    params = {
        "part": "snippet",
        "q": search_query,
        "maxResults": MAX_RESULTS,
        "type": "video",
        "key": API_KEY
    }
    resp = requests.get(url, params=params)
    if resp.status_code == 200:
        items = resp.json().get("items", [])
        # Fallback: if no items, try a more general search using the first word
        if not items:
            fallback_query = search_query.split()[0]
            st.info("No exact matches found. Showing similar videos.")
            params["q"] = fallback_query
            resp = requests.get(url, params=params)
            if resp.status_code == 200:
                items = resp.json().get("items", [])
        return [item["id"]["videoId"] for item in items if "videoId" in item["id"]]
    else:
        st.error("⚠️ Error fetching search results from YouTube.")
        return []

def fetch_video_details(video_ids):
    if not video_ids:
        return []
    url = "https://www.googleapis.com/youtube/v3/videos"
    params = {
        "part": "snippet,statistics,contentDetails",
        "id": ",".join(video_ids),
        "key": API_KEY
    }
    resp = requests.get(url, params=params)
    if resp.status_code == 200:
        items = resp.json().get("items", [])
        results = []
        for item in items:
            snippet = item.get("snippet", {})
            statistics = item.get("statistics", {})
            content_details = item.get("contentDetails", {})
            video_id = item["id"]
            title = snippet.get("title", "No Title")
            description = snippet.get("description", "")
            thumbnail = snippet.get("thumbnails", {}).get("medium", {}).get("url", "")
            view_count = int(statistics.get("viewCount", "0")) if statistics.get("viewCount", "0").isdigit() else 0
            comment_count = int(statistics.get("commentCount", "0")) if statistics.get("commentCount", "0").isdigit() else 0
            length_val = parse_duration(content_details.get("duration", "PT0M"))
            rating = calculate_rating(view_count, comment_count, length_val)
            results.append({
                "video_id": video_id,
                "title": title,
                "description": description,
                "thumbnail": thumbnail,
                "views": view_count,
                "comments": comment_count,
                "length_min": length_val,
                "rating": rating,
                "url": f"https://www.youtube.com/embed/{video_id}"
            })
        return results
    else:
        st.error("⚠️ Error fetching video details from YouTube.")
        return []

def filter_and_sort_videos(videos, length_filter):
    filtered = [v for v in videos if in_length_range(v["length_min"], length_filter)]
    filtered.sort(key=lambda x: x["rating"], reverse=True)
    return filtered

# ============ POINTS & HISTORY HANDLING ============
def mark_video_watched(video):
    st.session_state.points += 20
    st.session_state.watched.append(video)

def add_to_watch_later(video):
    if video not in st.session_state.watch_later:
        st.session_state.watch_later.append(video)
        st.success(f"Added '{video['title']}' to Watch Later")

# ============ MAIN LOGIC ============
videos = []
if page == "Trending":
    trending_items = fetch_trending_videos(chosen_region)
    video_ids = [item["id"] for item in trending_items]
    videos = fetch_video_details(video_ids)
    videos = filter_and_sort_videos(videos, length_filter)
elif page == "Home":
    if search_clicked and query:
        if st.session_state.get("last_query") != query:
            st.session_state.points += 10  # Award points for a new search
            st.session_state.last_query = query
        video_ids = fetch_search_results(query)
        videos = fetch_video_details(video_ids)
        videos = filter_and_sort_videos(videos, length_filter)
elif page == "History":
    st.header("📜 Watch History")
    if st.session_state.watched:
        for vid in st.session_state.watched:
            st.markdown(f"**{vid['title']}** - {vid['length_min']:.1f} min | Rating: {vid['rating']:.1f}")
            st.video(vid["url"])
    else:
        st.write("No videos watched yet.")
elif page == "Watch Later":
    st.header("⏳ Watch Later")
    if st.session_state.watch_later:
        for vid in st.session_state.watch_later:
            st.markdown(f"**{vid['title']}**")
            st.video(vid["url"])
    else:
        st.write("No videos saved for later.")

# ============ DISPLAY VIDEOS ============
if page in ["Home", "Trending"]:
    st.header("📌 Recommended Videos")
    if videos:
        for vid in videos:
            col1, col2 = st.columns([1, 4], gap="small")
            with col1:
                st.image(vid["thumbnail"], width=220)
            with col2:
                st.markdown(
                    f"""
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <span class="video-title" style="font-size: 1.25rem; font-weight: bold;">{vid["title"]}</span>
                        <div>
                            <p style="margin: 0; font-size: 0.8rem; color: #fff;">Rating</p>
                            <div style="background-color: #E53E3E; width: 45px; height: 45px; border-radius: 50%; color: #fff; display: flex; justify-content: center; align-items: center; margin-left: 10px;">
                                {vid["rating"]:.1f}
                            </div>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
                st.write(vid["description"][:200] + "...")
                st.write(f"👀 {vid['views']} views | 💬 {vid['comments']} comments | ⏳ {vid['length_min']:.1f} min")
                st.markdown(
                    f"""
                    <div class="video-container">
                        <iframe src="https://www.youtube.com/embed/{vid['video_id']}" frameborder="0" allowfullscreen></iframe>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
                if st.button(f"Watch Later - {vid['title']}", key=f"watchLater_{vid['video_id']}"):
                    add_to_watch_later(vid)
                if st.button(f"Mark '{vid['title']}' as Watched", key=f"watched_{vid['video_id']}"):
                    mark_video_watched(vid)
    else:
        if page == "Trending":
            st.write("❌ No trending videos found.")
        else:
            st.write("🔎 Enter a search term or choose 'Trending' to explore videos!")
