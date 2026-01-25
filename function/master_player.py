import vlc
import os

def load_to_master(self, audio_path, display_name, duration):
    """Load audio data and auto-play"""
    try:
        media = self.instance.media_new(audio_path)
        self.player.set_media(media)
        
        self.master_current_file = audio_path
        self.master_duration = duration
        self.is_paused = False
        
        self.lbl_now_playing.configure(text=f"Playing: {display_name}", text_color="#2ecc71")
        self.master_progress.configure(to=duration)
        self.master_progress.set(0)
        
        mins, secs = divmod(int(duration), 60)
        self.lbl_time.configure(text=f"00:00 / {mins:02d}:{secs:02d}")
        
        self.player.play()
        self.player.audio_set_volume(int(self.master_vol.get()))
        self.master_play_btn.configure(text="⏸")
        
    except Exception as e:
        print(f"VLC load error: {e}")

def toggle_master_playback(self):
    """Use only a single button for Play/Pause"""
    if not self.player.get_media():
        return

    if self.player.is_playing():
        self.player.pause()
        self.is_paused = True
        self.master_play_btn.configure(text="▶")
    else:
        self.player.play()
        self.is_paused = False
        self.master_play_btn.configure(text="⏸")

def seek_audio(self, event=None):
    """Handle accurate audio seeking"""
    if not self.player.get_media():
        return
        
    try:
        # Get current value from slider
        new_pos_secs = self.master_progress.get()
        
        # Set position for VLC (unit: ms)
        self.player.set_time(int(new_pos_secs * 1000))
        
        # Important: If it was paused when seeking, let the user decide
        # whether to click Play again, or auto-resume playback:
        if self.is_paused:
            self.player.play()
            self.is_paused = False
            self.master_play_btn.configure(text="⏸")
            
        # Return update rights to update_progress_loop
        self.is_dragging = False 
    except Exception as e:
        print(f"Seek error: {e}")
        self.is_dragging = False

def update_progress_loop(self):
    """Continuously update interface"""
    is_dragging = getattr(self, 'is_dragging', False)
    
    # 1. Update position if playing and not being dragged by user
    if self.player.is_playing() and not is_dragging:
        pos_ms = self.player.get_time()
        if pos_ms != -1:
            current_secs = pos_ms / 1000.0
            self.master_progress.set(current_secs)
            
            if hasattr(self, 'master_duration'):
                curr_min, curr_sec = divmod(int(current_secs), 60)
                max_min, max_sec = divmod(int(self.master_duration), 60)
                self.lbl_time.configure(text=f"{curr_min:02d}:{curr_sec:02d} / {max_min:02d}:{max_sec:02d}")

    # 2. Check end state to reset button
    state = self.player.get_state()
    if state == vlc.State.Ended:
        self.player.stop() # Internal stop to return to beginning
        self.master_play_btn.configure(text="▶")
        self.is_paused = True
        
        # Call callback to play next segment (if any)
        if hasattr(self, 'on_playlist_end') and callable(self.on_playlist_end):
            self.on_playlist_end()

    # 3. Always update volume
    if hasattr(self, 'master_vol'):
        self.player.audio_set_volume(int(self.master_vol.get()))

    self.after(100, self.update_progress_loop)