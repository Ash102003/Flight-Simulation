import streamlit as st
import pydeck as pdk
import pandas as pd
import time
import math
from collections import deque

st.set_page_config(layout="wide")

# ---------------- BFS WITH STEPS ----------------
def bfs_with_steps(graph, start, goal):
    queue = deque([[start]])
    visited = set()
    visited_order = []

    while queue:
        path = queue.popleft()
        node = path[-1]

        visited_order.append(node)

        if node == goal:
            return path, visited_order

        if node not in visited:
            visited.add(node)
            for neighbor in graph[node]:
                queue.append(path + [neighbor])

    return None, visited_order


# ---------------- BEARING ----------------
def get_bearing(p1, p2):
    lat1, lon1 = math.radians(p1[0]), math.radians(p1[1])
    lat2, lon2 = math.radians(p2[0]), math.radians(p2[1])

    dlon = lon2 - lon1

    x = math.sin(dlon) * math.cos(lat2)
    y = math.cos(lat1)*math.sin(lat2) - math.sin(lat1)*math.cos(lat2)*math.cos(dlon)

    return math.degrees(math.atan2(x, y))


# ---------------- HAVERSINE ----------------
def haversine(p1, p2):
    R = 6371  # km

    lat1, lon1 = math.radians(p1[0]), math.radians(p1[1])
    lat2, lon2 = math.radians(p2[0]), math.radians(p2[1])

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = math.sin(dlat/2)**2 + math.cos(lat1)*math.cos(lat2)*math.sin(dlon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

    return R * c


# ---------------- DATA ----------------
cities = {
    "Delhi": (28.6139, 77.2090),
    "Mumbai": (19.0760, 72.8777),
    "Chandigarh": (30.7333, 76.7794),
    "Bangalore": (12.9716, 77.5946),
    "Kolkata": (22.5726, 88.3639),
    "Jaipur": (26.9124, 75.7873),
    "Lucknow": (26.8467, 80.9462)
}

graph = {
    "Delhi": ["Chandigarh", "Jaipur", "Lucknow"],
    "Chandigarh": ["Delhi"],
    "Jaipur": ["Delhi", "Mumbai"],
    "Mumbai": ["Jaipur", "Bangalore"],
    "Bangalore": ["Mumbai", "Kolkata"],
    "Kolkata": ["Bangalore", "Lucknow"],
    "Lucknow": ["Delhi", "Kolkata"]
}


# ---------------- INTERPOLATION ----------------
def interpolate(p1, p2, steps=100):
    return [
        (
            p1[0] + (p2[0] - p1[0]) * t / steps,
            p1[1] + (p2[1] - p1[1]) * t / steps
        )
        for t in range(steps)
    ]


# ---------------- UI ----------------
st.title("✈️ Flight Simulation")

start = st.selectbox("Source", list(cities.keys()))
end = st.selectbox("Destination", list(cities.keys()))
flight_speed = st.slider("Flight Speed (km/h)", 400, 1000, 800)


if st.button("Start Simulation"):

    # BFS
    path, visited_nodes = bfs_with_steps(graph, start, end)

    if not path:
        st.error("No route found!")
        st.stop()

    # ---------------- BFS OUTPUT ----------------
    st.subheader("🧠 BFS Traversal")
    st.write("Visited Order:", visited_nodes)

    st.subheader("🌐 Graph Representation")
    st.json(graph)

    st.subheader("📍 Shortest Path (BFS)")
    st.write(" → ".join(path))
    st.info("BFS guarantees shortest path in an unweighted graph")

    # ---------------- DISTANCE ----------------
    total_distance = 0
    for i in range(len(path)-1):
        total_distance += haversine(cities[path[i]], cities[path[i+1]])

    st.subheader("📏 Total Distance")
    st.write(f"{total_distance:.2f} km")

    # ---------------- TIME ----------------
    time_taken = total_distance / flight_speed

    st.subheader("⏱ Estimated Flight Time")
    st.write(f"{time_taken:.2f} hours")

    # ---------------- MAP SETUP ----------------
    placeholder = st.empty()

    full_path = []
    for i in range(len(path) - 1):
        full_path.extend(interpolate(cities[path[i]], cities[path[i+1]]))

    city_df = pd.DataFrame([
        {"lat": v[0], "lon": v[1]}
        for v in cities.values()
    ])

    city_layer = pdk.Layer(
        "ScatterplotLayer",
        data=city_df,
        get_position='[lon, lat]',
        get_color=[0, 255, 100],
        get_radius=30000,
    )

    # ---------------- ANIMATION ----------------
    for i in range(len(full_path)):

        current = full_path[i]

        if i < len(full_path) - 1:
            angle = get_bearing(full_path[i], full_path[i+1])
        else:
            angle = 0

        path_layer = pdk.Layer(
            "PathLayer",
            data=[{"path": full_path[:i+1]}],
            get_path="path",
            get_color=[0, 150, 255],
            width_scale=5,
            width_min_pixels=3,
        )

        icon_data = pd.DataFrame([{
            "lat": current[0],
            "lon": current[1],
            "icon": {
                "url": "https://img.icons8.com/emoji/96/airplane-emoji.png",
                "width": 128,
                "height": 128,
                "anchorY": 64
            }
        }])

        plane_layer = pdk.Layer(
            "IconLayer",
            data=icon_data,
            get_icon="icon",
            get_position='[lon, lat]',
            get_size=5,
            size_scale=15,
            get_angle=angle,
        )

        deck = pdk.Deck(
            layers=[path_layer, city_layer, plane_layer],
            initial_view_state=pdk.ViewState(
                latitude=22,
                longitude=78,
                zoom=4.5,
                pitch=45,
            ),
            map_style="light",
        )

        placeholder.pydeck_chart(deck)
        time.sleep(0.02)

    st.success("Flight Completed ✈️")


# ---------------- REAL WORLD ----------------
st.subheader("📚 Real-world Applications")
st.write("""
- Flight route planning systems  
- GPS navigation  
- Internet routing (shortest path)  
- Social network analysis  
""")