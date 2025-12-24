import os
import requests
import json
from mcp.server.fastmcp import FastMCP, Context

# Configuration
# Users must provide the cookie via environment variable
COOKIES = os.environ.get("LUCKY_VOICE_COOKIE")

# Initialize FastMCP Server
mcp = FastMCP("Lucky Voice Karaoke")

class LuckyVoiceAPI:
    ENDPOINT = "https://www.luckyvoicekaraoke.com/graphql"
    HEADERS = {
        "Content-Type": "application/json",
        "User-Agent": "LuckyVoiceMCP/1.0",
        "Cookie": COOKIES or ""
    }

    def _query(self, query: str, variables: dict = None):
        if not self.HEADERS["Cookie"]:
             raise ValueError("LUCKY_VOICE_COOKIE environment variable is not set.")
             
        response = requests.post(self.ENDPOINT, headers=self.HEADERS, json={"query": query, "variables": variables or {}})
        if response.status_code != 200:
            raise Exception(f"API Request failed: {response.text}")
        
        data = response.json()
        if "errors" in data:
            raise Exception(f"GraphQL Error: {json.dumps(data['errors'])}")
            
        return data.get("data", {})

    def search(self, query_str: str, limit: int = 20):
        q = """
        query Query($query: String!, $limit: Int!) {
            search: searchSongs(query: $query, maxResults: $limit) {
                songs: results {
                    id
                    artistName: artist_name
                    title
                    duration
                }
            }
        }
        """
        data = self._query(q, {"query": query_str, "limit": limit})
        return data.get("search", {}).get("songs", [])

    def get_playlist_details(self, playlist_id: str):
        q = """
        query Playlist($id: ID!) {
            playlist(id: $id) {
                id
                name
                count
                songs {
                    id
                    title
                    artistName: artist_name
                    duration
                }
            }
        }
        """
        data = self._query(q, {"id": playlist_id})
        return data.get("playlist")

    def create_playlist(self, name: str):
        q = """
        mutation Mutation($playlist: PlaylistInput!) {
            playlist: createPlaylist(playlist: $playlist) {
                id
                name
                count
            }
        }
        """
        data = self._query(q, {"playlist": {"name": name, "songs": []}})
        return data.get("playlist")

    def delete_playlist(self, playlist_id: str):
        q = """
        mutation Mutation($id: ID!) {
            deletePlaylist(id: $id)
        }
        """
        data = self._query(q, {"id": playlist_id})
        return data.get("deletePlaylist")

    def update_playlist_songs(self, playlist_id: str, name: str, song_ids: list[str]):
        q = """
        mutation Mutation($id: ID!, $playlist: PlaylistInput!) {
            playlist: patchPlaylist(id: $id, playlist: $playlist) {
                id
                count
                songs { id }
            }
        }
        """
        data = self._query(q, {"id": playlist_id, "playlist": {"name": name, "songs": song_ids}})
        return data.get("playlist")

api = LuckyVoiceAPI()

# --- Tools ---

@mcp.tool()
def search_songs(query: str) -> str:
    """Search for songs by title or artist."""
    songs = api.search(query)
    if not songs:
        return "No songs found."
    
    result = []
    for s in songs:
        result.append(f"ID: {s['id']} | {s['title']} - {s['artistName']} ({s['duration']}s)")
    return "\n".join(result)

@mcp.tool()
def create_playlist(name: str) -> str:
    """Create a new empty playlist."""
    pl = api.create_playlist(name)
    return f"Created playlist '{pl['name']}' with ID: {pl['id']}"

@mcp.tool()
def delete_playlist(playlist_id: str) -> str:
    """Delete a playlist by its ID."""
    success = api.delete_playlist(playlist_id)
    return f"Playlist {playlist_id} deleted: {success}"

@mcp.tool()
def get_playlist_details(playlist_id: str) -> str:
    """Get details and songs of a playlist."""
    pl = api.get_playlist_details(playlist_id)
    if not pl:
        return f"Playlist {playlist_id} not found."
    
    output = [f"Playlist: {pl['name']} (ID: {pl['id']})", f"Song Count: {pl['count'] or 0}", "---"]
    for s in pl.get('songs', []):
        output.append(f"- [ID: {s['id']}] {s['title']} by {s['artistName']}")
    return "\n".join(output)

@mcp.tool()
def add_song_to_playlist(playlist_id: str, song_id: str) -> str:
    """Add a specific song to a playlist. Persists existing songs."""
    pl = api.get_playlist_details(playlist_id)
    if not pl:
        return "Playlist not found."
    
    current_ids = [s['id'] for s in pl.get('songs', [])]
    
    if song_id in current_ids:
        return "Song already in playlist."
    
    current_ids.append(song_id)
    
    updated = api.update_playlist_songs(playlist_id, pl['name'], current_ids)
    return f"Added song {song_id} to playlist {playlist_id}. Total songs: {updated.get('count')}"

@mcp.tool()
def remove_song_from_playlist(playlist_id: str, song_id: str) -> str:
    """Remove a specific song from a playlist."""
    pl = api.get_playlist_details(playlist_id)
    if not pl:
        return "Playlist not found."
    
    current_ids = [s['id'] for s in pl.get('songs', [])]
    
    if song_id not in current_ids:
        return "Song not in playlist."
    
    current_ids.remove(song_id)
    
    updated = api.update_playlist_songs(playlist_id, pl['name'], current_ids)
    return f"Removed song {song_id} from playlist {playlist_id}. Total songs: {updated.get('count')}"

# --- Bulk Operations ---

@mcp.tool()
def copy_playlist_songs(source_playlist_id: str, target_playlist_id: str) -> str:
    """Copy all songs from source playlist to target playlist."""
    source = api.get_playlist_details(source_playlist_id)
    if not source:
        return f"Source playlist {source_playlist_id} not found."
    
    source_ids = [s['id'] for s in source.get('songs', [])]
    if not source_ids:
        return "Source playlist is empty."

    target = api.get_playlist_details(target_playlist_id)
    if not target:
        return f"Target playlist {target_playlist_id} not found."
    
    target_ids = [s['id'] for s in target.get('songs', [])]

    new_ids = target_ids + [sid for sid in source_ids if sid not in target_ids]
    
    if len(new_ids) == len(target_ids):
        return "All songs from source are already in target."

    api.update_playlist_songs(target_playlist_id, target['name'], new_ids)
    return f"Copied {len(new_ids) - len(target_ids)} new songs from '{source['name']}' to '{target['name']}'."

@mcp.tool()
def sort_playlist(playlist_id: str, criteria: str = "artist") -> str:
    """
    Sort songs in a playlist.
    criteria: 'artist', 'title', 'duration', 'random'
    """
    import random
    
    pl = api.get_playlist_details(playlist_id)
    if not pl:
        return "Playlist not found."
    
    songs = pl.get('songs', [])
    if not songs:
        return "Playlist is empty."
    
    if criteria == "artist":
        songs.sort(key=lambda x: x['artistName'].lower())
    elif criteria == "title":
        songs.sort(key=lambda x: x['title'].lower())
    elif criteria == "duration":
        songs.sort(key=lambda x: x['duration'])
    elif criteria == "random":
        random.shuffle(songs)
    else:
        return f"Unknown criteria '{criteria}'. Use: artist, title, duration, random"
    
    new_ids = [s['id'] for s in songs]
    
    api.update_playlist_songs(playlist_id, pl['name'], new_ids)
    return f"Sorted playlist '{pl['name']}' by {criteria}."

# --- Resources ---

@mcp.resource("luckyvoice://playlists")
def list_playlists() -> str:
    """List all playlists for the current user."""
    # Attempting the 'me' query hypothesis.
    try:
        q = """
        query {
            me {
                playlists {
                    id
                    name
                    count
                }
            }
        }
        """
        if not api.HEADERS["Cookie"]:
             return "Error: No Cookie set."
             
        response = requests.post(api.ENDPOINT, headers=api.HEADERS, json={"query": q})
        data = response.json().get("data", {})
        
        playlists = data.get("me", {}).get("playlists", [])
        
        if not playlists:
            return "No playlists found or query structure differs."
            
        return json.dumps(playlists, indent=2)
    except Exception as e:
        return f"Error fetching playlists: {str(e)}"

if __name__ == "__main__":
    mcp.run()
