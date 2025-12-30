import os
import sys
import subprocess
import importlib.util
import tkinter as tk
from tkinter import ttk, messagebox
import threading
import json
import time
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Function to check and install required packages
def ensure_dependencies():
    required_packages = [
        "spotipy",
        "ytmusicapi",
        "requests",
        "concurrent.futures"  # This is in the standard library for Python 3.2+
    ]
    
    missing_packages = []
    
    # Check which packages are missing
    for package in required_packages:
        if package == "concurrent.futures" and sys.version_info >= (3, 2):
            # concurrent.futures is included in Python 3.2+
            continue
            
        if importlib.util.find_spec(package) is None:
            missing_packages.append(package)
    
    # If packages are missing, install them
    if missing_packages:
        print(f"Installing missing dependencies: {', '.join(missing_packages)}")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install"] + missing_packages)
            print("Dependencies installed successfully!")
            return True
        except subprocess.CalledProcessError:
            print("Failed to install dependencies. Please install manually: pip install " + " ".join(missing_packages))
            return False
    
    return True

# Create simple loading window
def show_loading_window():
    root = tk.Tk()
    root.title("Loading")
    root.geometry("300x100")
    root.resizable(False, False)
    
    frame = ttk.Frame(root, padding="10")
    frame.pack(fill=tk.BOTH, expand=True)
    
    ttk.Label(frame, text="Installing required packages...").pack(pady=5)
    
    progress = ttk.Progressbar(frame, orient=tk.HORIZONTAL, length=280, mode='indeterminate')
    progress.pack(pady=10)
    progress.start()
    
    status_var = tk.StringVar(value="Please wait...")
    status = ttk.Label(frame, textvariable=status_var)
    status.pack(pady=5)
    
    return root, status_var

# Check dependencies before importing them
if __name__ == "__main__":
    loading_window = None
    status_var = None
    
    # Show loading window only if we need to install packages
    try:
        # Quick check without starting the loading window
        needs_install = False
        for pkg in ["spotipy", "ytmusicapi", "requests"]:
            if importlib.util.find_spec(pkg) is None:
                needs_install = True
                break
        
        if needs_install:
            loading_window, status_var = show_loading_window()
            
            def install_thread():
                success = ensure_dependencies()
                if success:
                    status_var.set("Dependencies installed successfully! Starting application...")
                    loading_window.after(1000, loading_window.destroy)
                else:
                    status_var.set("Failed to install dependencies.")
                    loading_window.after(3000, loading_window.destroy)
                    sys.exit(1)
            
            threading.Thread(target=install_thread, daemon=True).start()
            loading_window.mainloop()
        
        # Now we can safely import the required modules
        import spotipy
        from spotipy.oauth2 import SpotifyOAuth
        from ytmusicapi import YTMusic, setup
        import socket
        import webbrowser
        import concurrent.futures
        from tkinter import scrolledtext, filedialog
        
    except Exception as e:
        if loading_window:
            loading_window.destroy()
        messagebox.showerror("Error", f"Failed to initialize: {str(e)}")
        sys.exit(1)

# Redirect console output to GUI
class TextRedirector:
    def __init__(self, text_widget):
        self.text_widget = text_widget
        self.buffer = ""

    def write(self, string):
        self.buffer += string
        if '\n' in self.buffer:
            self.text_widget.configure(state=tk.NORMAL)
            self.text_widget.insert(tk.END, self.buffer)
            self.text_widget.see(tk.END)
            self.text_widget.configure(state=tk.DISABLED)
            self.buffer = ""

    def flush(self):
        if self.buffer:
            self.text_widget.configure(state=tk.NORMAL)
            self.text_widget.insert(tk.END, self.buffer)
            self.text_widget.see(tk.END)
            self.text_widget.configure(state=tk.DISABLED)
            self.buffer = ""

class SpotifyToYTMusicApp:
    def __init__(self, root):
        self.root = root
        root.title("Spotify to YouTube Music Transfer")
        root.geometry("700x550")
        root.minsize(500, 400)
        
        # Config files and default credentials
        self.config_file = "spotify_config.json"
        self.client_id = os.getenv("SPOTIFY_CLIENT_ID")
        self.client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")
        self.redirect_uri = "http://localhost:8888/callback"
        self.spotify_token_info = None
        
        # Load config if it exists
        self.load_config()
        
        self.create_widgets()
        
    def create_widgets(self):
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # YouTube Music playlist info
        playlist_frame = ttk.LabelFrame(main_frame, text="YouTube Music Playlist", padding="10")
        playlist_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(playlist_frame, text="Playlist Name:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.playlist_name_var = tk.StringVar(value="Spotify Liked Songs")
        ttk.Entry(playlist_frame, textvariable=self.playlist_name_var, width=50).grid(row=0, column=1, sticky=tk.W, pady=2)
        
        ttk.Label(playlist_frame, text="Description:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.playlist_desc_var = tk.StringVar(value="Transferred from Spotify liked songs")
        ttk.Entry(playlist_frame, textvariable=self.playlist_desc_var, width=50).grid(row=1, column=1, sticky=tk.W, pady=2)
        
        # Options frame
        options_frame = ttk.LabelFrame(main_frame, text="Transfer Options", padding="10")
        options_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(options_frame, text="Parallel Workers:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.workers_var = tk.IntVar(value=5)
        ttk.Spinbox(options_frame, from_=1, to=20, textvariable=self.workers_var, width=5).grid(row=0, column=1, sticky=tk.W, pady=2)
        
        # Authentication buttons
        auth_frame = ttk.Frame(main_frame)
        auth_frame.pack(fill=tk.X, pady=5)
        
        self.spotify_auth_button = ttk.Button(auth_frame, text="Authenticate Spotify", command=self.authenticate_spotify)
        self.spotify_auth_button.pack(side=tk.LEFT, padx=5)
        
        self.ytmusic_auth_button = ttk.Button(auth_frame, text="Setup YouTube Music", command=self.setup_ytmusic_auth)
        self.ytmusic_auth_button.pack(side=tk.LEFT, padx=5)
        
        # Help button for YouTube Music setup
        self.ytmusic_help_button = ttk.Button(auth_frame, text="YouTube Music Setup Help", command=self.show_ytmusic_help)
        self.ytmusic_help_button.pack(side=tk.LEFT, padx=5)
        
        # Transfer button
        self.transfer_button = ttk.Button(main_frame, text="Start Transfer", command=self.start_transfer)
        self.transfer_button.pack(pady=10)
        
        # Progress bar
        self.progress = ttk.Progressbar(main_frame, orient=tk.HORIZONTAL, length=100, mode='indeterminate')
        self.progress.pack(fill=tk.X, pady=5)
        
        # Output console
        console_frame = ttk.LabelFrame(main_frame, text="Progress Log", padding="10")
        console_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.console = scrolledtext.ScrolledText(console_frame, wrap=tk.WORD, state=tk.DISABLED)
        self.console.pack(fill=tk.BOTH, expand=True)
        
        # Status bar
        self.status_var = tk.StringVar(value="Ready - Please authenticate with Spotify and YouTube Music before starting transfer")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)

        # Update status based on saved tokens
        if self.spotify_token_info:
            self.spotify_auth_button.configure(text="✓ Spotify Authenticated")
            
        if os.path.exists('headers_auth.json'):
            self.ytmusic_auth_button.configure(text="✓ YouTube Music Authenticated")

    def load_config(self):
        """Load Spotify configuration if it exists"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    if 'token_info' in config:
                        self.spotify_token_info = config['token_info']
                    print("Loaded existing Spotify authentication")
        except Exception as e:
            print(f"Error loading config: {e}")
    
    def save_config(self):
        """Save Spotify token information"""
        config = {
            'token_info': self.spotify_token_info
        }
        try:
            with open(self.config_file, 'w') as f:
                json.dump(config, f)
        except Exception as e:
            print(f"Error saving config: {e}")
    
    def authenticate_spotify(self):
        """Handle Spotify authentication with OAuth flow"""
        self.status_var.set("Starting Spotify authentication...")
        
        def start_auth_server():
            # Create a simple HTTP server to capture the OAuth callback
            server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server_socket.bind(('localhost', 8888))
            server_socket.listen(1)
            
            print("Waiting for Spotify OAuth callback...")
            client_connection, client_address = server_socket.accept()
            
            # Get the authorization code from the request
            request = client_connection.recv(1024).decode('utf-8')
            code = None
            
            for line in request.split('\n'):
                if "GET" in line and "callback?code=" in line:
                    code = line.split("code=")[1].split(" ")[0]
                    break
            
            # Send a response back to the browser
            response = "HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n"
            response += "<html><body><h1>Authentication Successful!</h1>"
            response += "<p>You can now close this window and return to the application.</p></body></html>"
            client_connection.sendall(response.encode('utf-8'))
            client_connection.close()
            server_socket.close()
            
            return code
        
        def auth_thread():
            try:
                # Set up the authorization URL
                auth = SpotifyOAuth(
                    client_id=self.client_id,
                    client_secret=self.client_secret,
                    redirect_uri=self.redirect_uri,
                    scope="user-library-read"
                )
                
                # Get the authorization URL
                auth_url = auth.get_authorize_url()
                
                # Open the authorization URL in the browser
                webbrowser.open(auth_url)
                
                # Start a simple server to handle the callback
                code = start_auth_server()
                
                if code:
                    # Exchange the code for a token
                    token_info = auth.get_access_token(code)
                    self.spotify_token_info = token_info
                    self.save_config()
                    
                    self.root.after(0, lambda: self.status_var.set("Spotify authentication successful!"))
                    self.root.after(0, lambda: self.spotify_auth_button.configure(text="✓ Spotify Authenticated"))
                    print("Spotify authentication successful!")
                else:
                    self.root.after(0, lambda: self.status_var.set("Spotify authentication failed!"))
                    print("Failed to get authorization code from Spotify")
            except Exception as e:
                self.root.after(0, lambda: self.status_var.set(f"Spotify authentication error: {str(e)}"))
                print(f"Authentication error: {str(e)}")
        
        # Start the authentication in a separate thread
        threading.Thread(target=auth_thread, daemon=True).start()
    
    def show_ytmusic_help(self):
        """Show a help window with YouTube Music setup instructions"""
        help_window = tk.Toplevel(self.root)
        help_window.title("YouTube Music Setup Instructions")
        help_window.geometry("650x500")
        help_window.grab_set()  # Make the window modal
        
        frame = ttk.Frame(help_window, padding="20")
        frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_label = ttk.Label(frame, text="How to Set Up YouTube Music Authentication", font=("TkDefaultFont", 12, "bold"))
        title_label.pack(pady=(0, 15))
        
        # Instructions in a scrolled text area
        instructions = scrolledtext.ScrolledText(frame, wrap=tk.WORD, width=60, height=20)
        instructions.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
        
        instructions.insert(tk.END, "Follow these steps to authenticate with YouTube Music:\n\n")
        instructions.insert(tk.END, "1. Open YouTube Music in your web browser (https://music.youtube.com)\n")
        instructions.insert(tk.END, "2. Make sure you are logged in to your YouTube/Google account\n")
        instructions.insert(tk.END, "3. Press F12 or right-click on the page and select 'Inspect' to open Developer Tools\n")
        instructions.insert(tk.END, "4. Select the 'Network' tab in Developer Tools\n")
        instructions.insert(tk.END, "5. Refresh the page\n")
        instructions.insert(tk.END, "6. Type 'next' or 'browse' in the filter field at the top of the Network tab\n")
        instructions.insert(tk.END, "7. Click one of the requests under the filtered results \n")
        instructions.insert(tk.END, "8. In the new panel that appears, select the 'Headers' tab\n")
        instructions.insert(tk.END, "9. Scroll down to the 'Request Headers' section\n")
        instructions.insert(tk.END, "10. Click the RAW toggle button to view the headers in raw format.\n")
        instructions.insert(tk.END, "11. Copy the data\n")
        instructions.insert(tk.END, "12. Click the 'Setup YouTube Music' button in the application\n")
        instructions.insert(tk.END, "13. When prompted, paste the copied value\n")
        instructions.insert(tk.END, "Note: The authentication process never sends your YouTube Music cookies to any third-party servers. All authentication data is stored locally on your computer.")
        
        instructions.configure(state=tk.DISABLED)  # Make it read-only
        
        # Close button
        close_button = ttk.Button(frame, text="Close", command=help_window.destroy)
        close_button.pack(pady=(0, 10))
    
    def setup_ytmusic_auth(self):
        """Guide the user through YouTube Music authentication"""
        self.status_var.set("Setting up YouTube Music authentication...")
        
        # Start by showing instructions in the console
        self.console.configure(state=tk.NORMAL)
        self.console.delete(1.0, tk.END)
        self.console.insert(tk.END, "YouTube Music Authentication Instructions:\n\n")
        self.console.insert(tk.END, "1. Open YouTube Music (music.youtube.com) in your browser\n")
        self.console.insert(tk.END, "2. Ensure you are logged in\n")
        self.console.insert(tk.END, "3. Press F12 to open developer tools\n")
        self.console.insert(tk.END, "4. Go to the Network tab\n")
        self.console.insert(tk.END, "5. Refresh the page\n")
        self.console.insert(tk.END, "6. Type 'browse' in the filter field\n")
        self.console.insert(tk.END, "7. Click on a request with 'browse' in the name\n")
        self.console.insert(tk.END, "8. Find the 'Request Headers' section\n")
        self.console.insert(tk.END, "9. Copy the entire 'Cookie' header value\n\n")
        self.console.insert(tk.END, "You'll be prompted to paste this value next.\n")
        self.console.insert(tk.END, "Then you'll need to copy and paste your 'User-Agent' value.\n\n")
        self.console.insert(tk.END, "Starting YouTube Music setup process...\n")
        self.console.configure(state=tk.DISABLED)
        
        def auth_thread():
            try:
                # Redirect stdout to our console
                old_stdout = sys.stdout
                sys.stdout = TextRedirector(self.console)
                
                # This will guide the user through the setup process
                setup(filepath='headers_auth.json')
                
                # Restore stdout
                sys.stdout = old_stdout
                
                # Try to verify the auth worked
                try:
                    ytmusic = YTMusic('headers_auth.json')
                    self.root.after(0, lambda: self.status_var.set("YouTube Music authentication successful!"))
                    self.root.after(0, lambda: self.ytmusic_auth_button.configure(text="✓ YouTube Music Authenticated"))
                    
                    # Add success message to console
                    self.console.configure(state=tk.NORMAL)
                    self.console.insert(tk.END, "\n✅ YouTube Music authentication successful!\n")
                    self.console.insert(tk.END, "You can now start the transfer process.\n")
                    self.console.configure(state=tk.DISABLED)
                    self.console.see(tk.END)
                except Exception as e:
                    self.root.after(0, lambda: self.status_var.set(f"YouTube Music authentication error: {str(e)}"))
                    
                    # Add error message to console
                    self.console.configure(state=tk.NORMAL)
                    self.console.insert(tk.END, f"\n❌ YouTube Music authentication error: {str(e)}\n")
                    self.console.insert(tk.END, "Please try again and make sure you copy the correct cookie value.\n")
                    self.console.configure(state=tk.DISABLED)
                    self.console.see(tk.END)
            except Exception as e:
                # Restore stdout
                sys.stdout = old_stdout
                self.root.after(0, lambda: self.status_var.set(f"YouTube Music authentication error: {str(e)}"))
                
                # Add error message to console
                self.console.configure(state=tk.NORMAL)
                self.console.insert(tk.END, f"\n❌ YouTube Music authentication error: {str(e)}\n")
                self.console.insert(tk.END, "Please try again and make sure you copied the correct values.\n")
                self.console.configure(state=tk.DISABLED)
                self.console.see(tk.END)
        
        # Start the authentication in a separate thread
        threading.Thread(target=auth_thread, daemon=True).start()

    def start_transfer(self):
        # Disable button during transfer
        self.transfer_button.configure(state=tk.DISABLED)
        self.progress.start()
        self.status_var.set("Starting transfer...")
        
        # Start transfer in separate thread
        thread = threading.Thread(target=self.run_transfer)
        thread.daemon = True
        thread.start()
    
    def run_transfer(self):
        # Redirect stdout to our console
        old_stdout = sys.stdout
        sys.stdout = TextRedirector(self.console)
        
        try:
            # Run the transfer
            self.transfer_spotify_to_ytmusic()
            
            self.status_var.set("Transfer completed!")
        except Exception as e:
            print(f"Error: {str(e)}")
            self.status_var.set(f"Error: {str(e)}")
        finally:
            # Restore stdout
            sys.stdout = old_stdout
            
            # Re-enable button
            self.root.after(0, lambda: self.transfer_button.configure(state=tk.NORMAL))
            self.root.after(0, self.progress.stop)
    
    def transfer_spotify_to_ytmusic(self):
        # Setup APIs
        sp = self.setup_spotify()
        ytmusic = self.setup_ytmusic()
        
        if not sp or not ytmusic:
            print("Failed to set up one or both APIs. Exiting.")
            return
        
        # Get Spotify liked songs
        tracks = self.get_spotify_liked_songs(sp)
        
        if not tracks:
            print("No tracks found in your Spotify liked songs or failed to fetch them.")
            return
        
        # Create YouTube Music playlist
        playlist_name = self.playlist_name_var.get()
        playlist_description = self.playlist_desc_var.get()
        playlist_id = self.create_ytmusic_playlist(ytmusic, playlist_name, playlist_description)
        
        if not playlist_id:
            print("Failed to create YouTube Music playlist.")
            return
        
        print(f"Created playlist with ID: {playlist_id}")
        
        # Search and add tracks to YouTube Music playlist in parallel
        max_workers = self.workers_var.get()
        added, not_found = self.search_and_add_to_playlist_parallel(ytmusic, playlist_id, tracks, max_workers)
        
        # Summary
        print("\n" + "="*50)
        print(f"Transfer completed!")
        print(f"Total tracks from Spotify: {len(tracks)}")
        print(f"Successfully added to YouTube Music: {added}")
        print(f"Not found or failed to add: {len(not_found)}")
        
        if not_found:
            print("\nThe following tracks couldn't be found or added:")
            for query in not_found[:20]:  # Show first 20 only if there are many
                print(f"- {query}")
            
            if len(not_found) > 20:
                print(f"...and {len(not_found) - 20} more")
            
            print("\nYou may want to search for these manually.")

    def setup_spotify(self):
        """Setup and authenticate with Spotify API using stored token"""
        if not self.spotify_token_info:
            print("No Spotify authentication found. Please click 'Authenticate Spotify' first.")
            return None
        
        try:
            auth_manager = SpotifyOAuth(
                client_id=self.client_id,
                client_secret=self.client_secret,
                redirect_uri=self.redirect_uri,
                scope="user-library-read",
                cache_handler=None  # Disable caching as we handle it ourselves
            )
            
            # Check if token is expired and refresh if needed
            if auth_manager.is_token_expired(self.spotify_token_info):
                print("Refreshing expired Spotify token...")
                self.spotify_token_info = auth_manager.refresh_access_token(
                    self.spotify_token_info['refresh_token']
                )
                self.save_config()
            
            # Create the client with the token info
            client = spotipy.Spotify(auth=self.spotify_token_info['access_token'])
            return client
        except Exception as e:
            print(f"Error connecting to Spotify: {e}")
            return None

    def setup_ytmusic(self):
        """Setup and authenticate with YouTube Music API"""
        try:
            if not os.path.exists('headers_auth.json'):
                print("YouTube Music authentication file not found. Please click 'Setup YouTube Music' first.")
                return None
                
            # Try to use existing auth
            ytmusic = YTMusic('headers_auth.json')
            return ytmusic
        except Exception as e:
            print(f"Error connecting to YouTube Music: {e}")
            return None

    def get_spotify_liked_songs(self, sp):
        """Get all liked songs from Spotify"""
        if not sp:
            return []
        
        print("Fetching your Spotify liked songs...")
        results = sp.current_user_saved_tracks(limit=50)
        tracks = results['items']
        
        # Pagination to get all liked songs
        while results['next']:
            results = sp.next(results)
            tracks.extend(results['items'])
            print(f"Fetched {len(tracks)} songs so far...")
            # Be nice to the API
            time.sleep(0.5)
        
        print(f"Total liked songs fetched from Spotify: {len(tracks)}")
        return tracks

    def create_ytmusic_playlist(self, ytmusic, name, description):
        """Create a new playlist on YouTube Music"""
        print(f"Creating new YouTube Music playlist: {name}")
        return ytmusic.create_playlist(name, description)

    def process_track(self, args):
        """Process a single track - for parallel processing"""
        ytmusic, playlist_id, item, index, total = args
        track = item['track']
        
        # Format search query
        artist = track['artists'][0]['name']
        song = track['name']
        query = f"{song} {artist}"
        
        result = {
            'query': query,
            'success': False,
            'song': song,
            'artist': artist
        }
        
        # Search on YouTube Music
        try:
            search_results = ytmusic.search(query, filter="songs")
            
            # Add first result to playlist if found
            if search_results:
                video_id = search_results[0]['videoId']
                ytmusic.add_playlist_items(playlist_id, [video_id])
                result['success'] = True
                print(f"✓ Added [{index+1}/{total}]: {song} by {artist}")
            else:
                print(f"× Not found [{index+1}/{total}]: {song} by {artist}")
        except Exception as e:
            result['error'] = str(e)
            print(f"× Error [{index+1}/{total}]: {song} by {artist} - {str(e)}")
        
        # Brief pause to avoid overwhelming the API
        time.sleep(0.3)
        
        return result

    def search_and_add_to_playlist_parallel(self, ytmusic, playlist_id, tracks, max_workers=5):
        """Search for tracks on YouTube Music and add to playlist in parallel"""
        total = len(tracks)
        print(f"Starting to add {total} tracks to YouTube Music using {max_workers} workers...")
        
        results = []
        
        # Create arguments for each track
        args_list = [(ytmusic, playlist_id, item, i, total) for i, item in enumerate(tracks)]
        
        # Process in parallel
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(self.process_track, args) for args in args_list]
            for future in concurrent.futures.as_completed(futures):
                results.append(future.result())
        
        # Count successes and failures
        added = sum(1 for r in results if r['success'])
        not_found = [r['query'] for r in results if not r['success']]
        
        return added, not_found

def main():
    # Create main application window
    root = tk.Tk()
    app = SpotifyToYTMusicApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
