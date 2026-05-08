import customtkinter as ctk
from tkinter import filedialog, messagebox
from threading import Thread
import time
import os
from dotenv import load_dotenv
from orchestrator import process_full_query
from ears import Listener
from mouth import speak
from brain import export_chat_to_txt

# Load environment variables
load_dotenv()
PICOVOICE_KEY = os.getenv("PICOVOICE_ACCESS_KEY")

class MessageBubble(ctk.CTkFrame):
    def __init__(self, master, role, text, colors, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        
        self.grid_columnconfigure(0, weight=1)
        
        timestamp = time.strftime("%H:%M")
        align = "e" if role == "YOU" else "w"
        bubble_color = colors["accent"] if role == "YOU" else colors["card"]
        text_color = "#FFFFFF" if role == "YOU" else colors["text"]
        
        # Bubble Container
        self.bubble = ctk.CTkFrame(
            self, 
            fg_color=bubble_color, 
            corner_radius=15,
            border_width=0 if role == "YOU" else 1,
            border_color=colors["border"]
        )
        self.bubble.grid(row=0, column=0, sticky=align, padx=10, pady=5)
        
        # Message Text
        self.label = ctk.CTkLabel(
            self.bubble, 
            text=text, 
            font=ctk.CTkFont(family="Inter", size=14),
            text_color=text_color,
            wraplength=500,
            justify="left"
        )
        self.label.pack(padx=15, pady=(10, 5))
        
        # Timestamp
        self.time_label = ctk.CTkLabel(
            self.bubble, 
            text=f"{role} • {timestamp}", 
            font=ctk.CTkFont(family="Inter", size=10),
            text_color=colors["secondary_text"] if role != "YOU" else "#E0E0E0"
        )
        self.time_label.pack(padx=15, pady=(0, 5), anchor=align)

class AssistantApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Setup Window
        self.title("Nexus AI Student Assistant")
        self.geometry("1200x900")
        
        # Initial Theme
        self.appearance_mode = "dark"
        ctk.set_appearance_mode(self.appearance_mode)
        
        # Professional Color Palette
        self.colors = {
            "dark": {
                "bg": "#0B0E14",
                "sidebar": "#161B22",
                "card": "#1C2128",
                "accent": "#238636", # Success Green for user or #58A6FF for blue
                "user_bubble": "#238636",
                "text": "#C9D1D9",
                "secondary_text": "#8b949e",
                "border": "#30363D",
                "input_bg": "#0D1117"
            },
            "light": {
                "bg": "#FFFFFF",
                "sidebar": "#F6F8FA",
                "card": "#FFFFFF",
                "accent": "#0969DA",
                "user_bubble": "#0969DA",
                "text": "#24292F",
                "secondary_text": "#57606a",
                "border": "#D0D7DE",
                "input_bg": "#F6F8FA"
            }
        }
        self.current_colors = self.colors["dark"]
        self.configure(fg_color=self.current_colors["bg"])

        # State Variables
        self.mode_var = ctk.StringVar(value="Normal Assistant")
        self.is_listening_manual = False
        self.last_file_uploaded = False
        self.message_widgets = []
        self.history_widgets = []
        
        # Layout
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # -----------------------------
        # 1. SIDEBAR
        # -----------------------------
        self.sidebar = ctk.CTkFrame(self, fg_color=self.current_colors["sidebar"], width=260, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_propagate(False)

        self.logo_label = ctk.CTkLabel(
            self.sidebar, 
            text="NEXUS AI", 
            font=ctk.CTkFont(family="Inter", size=24, weight="bold"),
            text_color=self.current_colors["accent"]
        )
        self.logo_label.pack(pady=30, padx=20)

        self.new_chat_btn = ctk.CTkButton(
            self.sidebar,
            text="+ New Chat",
            font=ctk.CTkFont(weight="bold"),
            fg_color=self.current_colors["card"],
            border_color=self.current_colors["border"],
            border_width=1,
            text_color=self.current_colors["text"],
            hover_color=self.current_colors["border"],
            command=self.clear_chat
        )
        self.new_chat_btn.pack(pady=10, padx=20, fill="x")

        # Sidebar Sections
        self.history_label = ctk.CTkLabel(self.sidebar, text="HISTORY", font=ctk.CTkFont(size=11, weight="bold"), text_color=self.current_colors["secondary_text"])
        self.history_label.pack(pady=(20, 5), padx=20, anchor="w")
        
        self.history_frame = ctk.CTkScrollableFrame(self.sidebar, fg_color="transparent")
        self.history_frame.pack(fill="both", expand=True, padx=5, pady=5)

        # Status indicator at bottom of sidebar
        self.sidebar_status = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self.sidebar_status.pack(side="bottom", fill="x", pady=20, padx=20)
        
        self.status_dot = ctk.CTkLabel(self.sidebar_status, text="●", text_color="#238636", font=ctk.CTkFont(size=14))
        self.status_dot.pack(side="left")
        
        self.status_text = ctk.CTkLabel(self.sidebar_status, text="System Ready", font=ctk.CTkFont(size=12), text_color=self.current_colors["secondary_text"])
        self.status_text.pack(side="left", padx=10)

        # -----------------------------
        # 2. MAIN CONTENT
        # -----------------------------
        self.main_container = ctk.CTkFrame(self, fg_color="transparent")
        self.main_container.grid(row=0, column=1, sticky="nsew")
        self.main_container.grid_columnconfigure(0, weight=1)
        self.main_container.grid_rowconfigure(1, weight=1)

        # Header
        self.header = ctk.CTkFrame(self.main_container, fg_color="transparent", height=70)
        self.header.grid(row=0, column=0, sticky="ew", padx=30, pady=10)
        self.header.grid_columnconfigure(1, weight=1)

        # Dynamic Mode Selector (Professional appearance)
        self.mode_menu = ctk.CTkSegmentedButton(
            self.header,
            values=["Normal Assistant", "Viva Mode", "Quiz Mode", "Study Notes Mode"],
            variable=self.mode_var,
            command=self.on_mode_change,
            selected_color=self.current_colors["accent"],
            font=ctk.CTkFont(size=13)
        )
        self.mode_menu.grid(row=0, column=1)

        # Header Actions
        self.header_actions = ctk.CTkFrame(self.header, fg_color="transparent")
        self.header_actions.grid(row=0, column=2)

        self.theme_btn = ctk.CTkButton(self.header_actions, text="🌙", width=40, fg_color="transparent", hover_color=self.current_colors["card"], command=self.toggle_theme)
        self.theme_btn.pack(side="left", padx=5)
        
        self.export_btn = ctk.CTkButton(self.header_actions, text="Export", width=60, fg_color="transparent", hover_color=self.current_colors["card"], command=self.export_chat)
        self.export_btn.pack(side="left", padx=5)

        # Chat Area
        self.chat_area = ctk.CTkScrollableFrame(
            self.main_container, 
            fg_color="transparent"
        )
        self.chat_area.grid(row=1, column=0, sticky="nsew", padx=30, pady=0)
        self.chat_area.grid_columnconfigure(0, weight=1)

        # -----------------------------
        # 3. DYNAMIC TOOLS PANEL (Contextual)
        # -----------------------------
        self.tools_panel = ctk.CTkFrame(self.main_container, fg_color="transparent", height=0)
        self.tools_panel.grid(row=2, column=0, sticky="ew", padx=40, pady=(10, 0))
        
        self.tool_content = ctk.CTkFrame(self.tools_panel, fg_color=self.current_colors["card"], corner_radius=12, border_width=1, border_color=self.current_colors["border"])
        self.tool_content.pack(fill="x", pady=5)
        
        # Placeholder for dynamic buttons
        self.active_tool_buttons = []

        # -----------------------------
        # 4. INPUT AREA
        # -----------------------------
        self.input_container = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.input_container.grid(row=3, column=0, sticky="ew", padx=30, pady=(10, 30))
        self.input_container.grid_columnconfigure(1, weight=1)

        self.input_bar = ctk.CTkFrame(
            self.input_container, 
            fg_color=self.current_colors["input_bg"],
            corner_radius=25,
            border_width=1,
            border_color=self.current_colors["border"]
        )
        self.input_bar.grid(row=0, column=0, columnspan=3, sticky="ew", padx=10)
        self.input_bar.grid_columnconfigure(1, weight=1)

        self.upload_btn = ctk.CTkButton(
            self.input_bar, text="+", width=40, height=40, 
            fg_color="transparent", hover_color=self.current_colors["card"], 
            font=ctk.CTkFont(size=20), command=self.upload_file
        )
        self.upload_btn.grid(row=0, column=0, padx=10, pady=5)

        self.user_entry = ctk.CTkEntry(
            self.input_bar, 
            placeholder_text="Message NEXUS...",
            height=50,
            border_width=0,
            fg_color="transparent",
            font=ctk.CTkFont(family="Inter", size=15)
        )
        self.user_entry.grid(row=0, column=1, sticky="ew")
        self.user_entry.bind("<Return>", lambda e: self.send_query())

        self.mic_btn = ctk.CTkButton(
            self.input_bar, text="🎤", width=40, height=40, 
            fg_color="transparent", hover_color=self.current_colors["card"], 
            command=self.manual_listen
        )
        self.mic_btn.grid(row=0, column=2, padx=5)

        self.send_btn = ctk.CTkButton(
            self.input_bar, text="➤", width=40, height=40, 
            fg_color=self.current_colors["accent"], hover_color="#1a632a",
            corner_radius=20, text_color="#FFFFFF", command=self.send_query
        )
        self.send_btn.grid(row=0, column=3, padx=10)

        # -----------------------------
        # INITIALIZATION
        # -----------------------------
        self.update_tool_panel() # Initial UI state
        
        try:
            self.listener = Listener(PICOVOICE_KEY)
            self.add_message("SYSTEM", "Nexus AI Ready. How can I help you today?")
            self.load_stored_chat()
            Thread(target=self.background_voice_loop, daemon=True).start()
        except Exception as e:
            self.add_message("SYSTEM", f"Initialization Error: {e}")
            self.update_status("Offline", "#f85149")

    # --- UI Logic Methods ---

    def on_mode_change(self, mode):
        self.update_tool_panel()
        self.add_message("SYSTEM", f"Switched to {mode}.")

    def update_tool_panel(self):
        # Clear existing buttons
        for btn in self.active_tool_buttons:
            btn.destroy()
        self.active_tool_buttons = []
        
        mode = self.mode_var.get()
        show_panel = False
        
        if mode == "Viva Mode":
            show_panel = True
            lbl = ctk.CTkLabel(self.tool_content, text="Viva Session Active •", text_color=self.current_colors["accent"], font=ctk.CTkFont(size=12, weight="bold"))
            lbl.pack(side="left", padx=20, pady=10)
            btn = ctk.CTkButton(self.tool_content, text="Start Viva", height=32, fg_color=self.current_colors["accent"], command=lambda: self.send_special_query("Start technical viva interview"))
            btn.pack(side="right", padx=10, pady=10)
            self.active_tool_buttons.extend([lbl, btn])
            
        elif mode == "Quiz Mode":
            show_panel = True
            lbl = ctk.CTkLabel(self.tool_content, text="Generate Quiz on:", font=ctk.CTkFont(size=12))
            lbl.pack(side="left", padx=(20, 5), pady=10)
            
            entry = ctk.CTkEntry(self.tool_content, placeholder_text="Topic...", height=30, width=150)
            entry.pack(side="left", padx=5)
            
            btn = ctk.CTkButton(self.tool_content, text="Generate", height=32, fg_color=self.current_colors["accent"], command=lambda: self.send_special_query(f"Generate quiz on {entry.get()}"))
            btn.pack(side="left", padx=10, pady=10)
            self.active_tool_buttons.extend([lbl, entry, btn])
            
        elif mode == "Study Notes Mode":
            if self.last_file_uploaded:
                show_panel = True
                lbl = ctk.CTkLabel(self.tool_content, text="Document Tools:", font=ctk.CTkFont(size=12, weight="bold"))
                lbl.pack(side="left", padx=20, pady=10)
                
                tools = [("Summarize", "Summarize content"), ("Study Notes", "Generate study notes"), ("Exam Qs", "Generate important questions")]
                for text, cmd in tools:
                    b = ctk.CTkButton(self.tool_content, text=text, height=30, width=100, fg_color="transparent", border_width=1, border_color=self.current_colors["border"], command=lambda c=cmd: self.send_special_query(c))
                    b.pack(side="left", padx=5)
                    self.active_tool_buttons.append(b)
                self.active_tool_buttons.append(lbl)
            else:
                show_panel = True
                lbl = ctk.CTkLabel(self.tool_content, text="Please upload a document to unlock study tools.", text_color=self.current_colors["secondary_text"])
                lbl.pack(pady=10)
                self.active_tool_buttons.append(lbl)
        
        if show_panel:
            self.tools_panel.grid()
        else:
            self.tools_panel.grid_remove()

    def add_message(self, role, text):
        bubble = MessageBubble(self.chat_area, role, text, self.current_colors)
        bubble.pack(fill="x", padx=10, pady=5)
        self.message_widgets.append(bubble)
        
        # Ensure UI updates before scrolling
        self.update_idletasks()
        self.after(100, lambda: self.chat_area._parent_canvas.yview_moveto(1.0))
        
        # Add to sidebar history if it's a model response
        if role == "ASSISTANT" and len(text) > 5:
            self.add_to_sidebar_history(text[:30] + "...")

    def add_to_sidebar_history(self, summary):
        btn = ctk.CTkButton(
            self.history_frame, 
            text=summary, 
            fg_color="transparent", 
            text_color=self.current_colors["secondary_text"],
            anchor="w",
            font=ctk.CTkFont(size=12),
            hover_color=self.current_colors["card"]
        )
        btn.pack(fill="x", pady=2)
        self.history_widgets.append(btn)

    def update_status(self, text, color="#238636"):
        self.status_text.configure(text=text)
        self.status_dot.configure(text_color=color)

    def toggle_theme(self):
        if self.appearance_mode == "dark":
            self.appearance_mode = "light"
            self.current_colors = self.colors["light"]
            self.theme_btn.configure(text="☀️")
        else:
            self.appearance_mode = "dark"
            self.current_colors = self.colors["dark"]
            self.theme_btn.configure(text="🌙")
        
        ctk.set_appearance_mode(self.appearance_mode)
        self.configure(fg_color=self.current_colors["bg"])
        self.sidebar.configure(fg_color=self.current_colors["sidebar"])
        self.tool_content.configure(fg_color=self.current_colors["card"], border_color=self.current_colors["border"])
        self.input_bar.configure(fg_color=self.current_colors["input_bg"], border_color=self.current_colors["border"])
        self.update_tool_panel()

    def export_chat(self):
        result = export_chat_to_txt()
        messagebox.showinfo("Export", result)

    def clear_chat(self):
        if messagebox.askyesno("New Chat", "Clear current conversation?"):
            from brain import clear_chat_history
            from orchestrator import reset_orchestrator
            
            clear_chat_history()
            reset_orchestrator()
            
            # Clear message bubbles safely
            for widget in self.message_widgets:
                try: widget.destroy()
                except: pass
            self.message_widgets = []
            
            # Clear sidebar history safely
            for widget in self.history_widgets:
                try: widget.destroy()
                except: pass
            self.history_widgets = []
            
            # Reset scroll position and region
            try:
                self.chat_area._parent_canvas.yview_moveto(0.0)
                self.chat_area._parent_canvas.configure(scrollregion=(0, 0, 0, 0))
            except: pass
            
            self.add_message("SYSTEM", "Conversation cleared. How can I help?")
            self.last_file_uploaded = False
            self.update_tool_panel()

    def load_stored_chat(self):
        from brain import chat_history
        if chat_history:
            for msg in chat_history:
                role = "YOU" if msg.get("role") == "user" else "ASSISTANT"
                text = msg["parts"][0]["text"]
                self.add_message(role, text)

    # --- Core Processing ---

    def send_query(self):
        query = self.user_entry.get().strip()
        if query:
            self.user_entry.delete(0, "end")
            self.process_request(query, False)

    def send_special_query(self, query):
        self.process_request(query, False)

    def upload_file(self):
        file_path = filedialog.askopenfilename()
        if file_path:
            self.last_file_uploaded = True
            self.add_message("SYSTEM", f"Uploading {os.path.basename(file_path)}...")
            self.process_request(f"analyze file {file_path}", False)
            self.update_tool_panel()

    def manual_listen(self):
        if self.is_listening_manual: return
        Thread(target=self._manual_listen_thread, daemon=True).start()

    def _manual_listen_thread(self):
        self.is_listening_manual = True
        self.update_status("Listening...", "#ffaa00")
        query = self.listener.listen_to_command()
        self.update_status("Ready", "#238636")
        self.is_listening_manual = False
        if query: self.process_request(query, True)

    def background_voice_loop(self):
        while True:
            if not self.is_listening_manual:
                try:
                    if self.listener.wait_for_wake_word():
                        self.update_status("Listening...", "#ffaa00")
                        query = self.listener.listen_to_command()
                        self.update_status("Ready", "#238636")
                        if query: self.process_request(query, True)
                except: time.sleep(1)
            time.sleep(0.5)

    def process_request(self, query, use_voice):
        role = "YOU (VOICE)" if use_voice else "YOU"
        self.add_message(role, query)
        self.update_status("Thinking...", self.current_colors["accent"])
        mode = self.mode_var.get()
        Thread(target=self._run_brain, args=(query, use_voice, mode), daemon=True).start()

    def _run_brain(self, query, use_voice, mode):
        try:
            response = process_full_query(query, ai_mode=mode)
            self.after(0, lambda: self.add_message("ASSISTANT", response))
            self.after(0, lambda: self.update_status("Ready", "#238636"))
            if use_voice: speak(response)
        except Exception as e:
            self.after(0, lambda: self.add_message("SYSTEM", f"Error: {e}"))
            self.after(0, lambda: self.update_status("Error", "#f85149"))

if __name__ == "__main__":
    app = AssistantApp()
    app.mainloop()

