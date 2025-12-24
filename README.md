# Lucky Voice Karaoke - MCP Server

An unofficial Model Context Protocol (MCP) server for managing Lucky Voice Karaoke playlists programmatically. This server exposes tools to AI agents (like Claude) to search songs, create playlists, and perform bulk operations like copying and sorting.

## Features

- **Search**: Find songs by Artist or Title.
- **Manage**: Create and Delete playlists.
- **Edit**: Add and Remove specific songs.
- **Bulk**:
  - `copy_playlist_songs`: Merge songs from one playlist to another.
  - `sort_playlist`: Auto-sort by Artist, Title, Duration, or Random.
- **Inspect**: View all your playlists and their contents.

## Installation

### Prerequisites
- Python 3.10 or higher
- A Lucky Voice Karaoke account (Active Subscription)

### 1. Clone & Install
```bash
git clone https://github.com/your-username/lucky-voice-mcp.git
cd lucky-voice-mcp
pip install -r requirements.txt
```

### 2. Get your Session Cookie
Since this is an unofficial tool, you must provide your own session cookie.
1. Open [Lucky Voice Karaoke](https://www.luckyvoicekaraoke.com/sing) in your browser.
2. Open Developer Tools (F12 or Cmd+Opt+I) -> Network Tab.
3. Refresh the page and click the first request partial (e.g., `sing` or `graphql`).
4. Copy the value of the `Cookie` request header.
5. **Keep this value secret!**

## Usage

### Local (Claude Desktop)
Add this to your `claude_desktop_config.json`:
```json
{
  "mcpServers": {
    "lucky-voice": {
      "command": "python3",
      "args": ["/absolute/path/to/lucky_voice_mcp.py"],
      "env": {
        "LUCKY_VOICE_COOKIE": "your_cookie_string_here"
      }
    }
  }
}
```

### Docker
```bash
# Build
docker build -t lucky-voice-mcp .

# Run
docker run -i --rm \
  -e LUCKY_VOICE_COOKIE="your_cookie_string_here" \
  lucky-voice-mcp
```

## Disclaimer
This project is unofficial and not affiliated with Lucky Voice. Use responsibly. The internal API may change at any time.

## License
MIT
