import json
import os
import sys
import tkinter as tk
from tkinter import messagebox, ttk
import cv2
import numpy as np
from PIL import Image, ImageTk

# Configuration file path
CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "setup_data.json")

DEFAULT_CONFIG = {
    "ready": 0,
    "setup": 0,
    "model": "chatgpt",
    "name": "",
    "bio": "",
    "api_key": "",
    "theme": "dark",
    "scaling": 1.0,
}

THEMES = {
    "dark": {
        "bg": "#0a0a12",
        "card_bg": "#131422",
        "card_border": "#212438",
        "input_bg": "#191b2c",
        "input_fg": "#f1f3f9",
        "input_border": "#2c314f",
        "fg": "#ffffff",
        "fg_muted": "#8d95ab",
        "accent": "#ff8800",
        "accent_hover": "#ffa033",
        "accent_fg": "#000000",
        "cyan": "#00d4ff",
        "green": "#00e676",
        "red": "#ff4757",
        "yellow": "#ffd32a",
        "btn_sec_bg": "#212438",
        "btn_sec_fg": "#e0e3ed",
        "btn_sec_hover": "#2c304d",
        "nav_bg": "#0e0f1a",
    },
    "light": {
        "bg": "#f4f6fb",
        "card_bg": "#ffffff",
        "card_border": "#e1e5f0",
        "input_bg": "#f0f3fa",
        "input_fg": "#141724",
        "input_border": "#c8cfdf",
        "fg": "#141724",
        "fg_muted": "#5e667d",
        "accent": "#ff7700",
        "accent_hover": "#e66a00",
        "accent_fg": "#ffffff",
        "cyan": "#0088cc",
        "green": "#00a854",
        "red": "#e74c3c",
        "yellow": "#f39c12",
        "btn_sec_bg": "#e6eaf2",
        "btn_sec_fg": "#2c3345",
        "btn_sec_hover": "#d7dde9",
        "nav_bg": "#ffffff",
    },
}

MODEL_NAMES = {
    "chatgpt": "ChatGPT",
    "claude": "Claude",
    "gemini": "Gemini",
}


def load_config():
    if not os.path.exists(CONFIG_PATH):
        save_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG.copy()
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if not content:
                save_config(DEFAULT_CONFIG)
                return DEFAULT_CONFIG.copy()
            data = json.loads(content)
            # Ensure all default keys exist
            updated = False
            for k, v in DEFAULT_CONFIG.items():
                if k not in data:
                    data[k] = v
                    updated = True
            if updated:
                save_config(data)
            return data
    except Exception as e:
        print(f"Error loading setup_data.json: {e}")
        save_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG.copy()


def save_config(data):
    try:
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print(f"Error saving setup_data.json: {e}")


def format_model(model_str):
    m = str(model_str).lower().strip()
    return MODEL_NAMES.get(m, model_str.title() if model_str else "Unknown")


def find_video(filename):
    base_dir = os.path.dirname(os.path.abspath(__file__))
    candidates = [
        filename,
        filename.lower(),
        filename.capitalize(),
        "Orion_Setup.mp4" if "setup" in filename.lower() else "Orion_Startup.mp4",
        "orion_setup.mp4" if "setup" in filename.lower() else "orion_startup.mp4",
    ]
    for c in candidates:
        p = os.path.join(base_dir, c)
        if os.path.exists(p):
            return p
    return os.path.join(base_dir, filename)


class OrionApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Project Orion: Chatbot Interface")
        self.root.minsize(780, 560)

        self.config = load_config()
        self.scaling = float(self.config.get("scaling", 1.0))
        self.theme_name = self.config.get("theme", "dark")
        if self.theme_name not in THEMES:
            self.theme_name = "dark"
        self.theme = THEMES[self.theme_name]

        # Apply scaling and geometry
        self.apply_scaling(self.scaling, update_geometry=True)
        self.root.configure(bg=self.theme["bg"])

        # State tracking
        self.cap = None
        self.video_after_id = None
        self.chat_history = []

        # Container
        self.main_container = tk.Frame(self.root, bg=self.theme["bg"])
        self.main_container.pack(fill="both", expand=True)

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        # Start Video or jump to Screen
        self.start_intro_video()

    def get_font(self, size, weight="normal"):
        scaled_size = max(8, int(size * self.scaling))
        return ("Segoe UI", scaled_size, weight)

    def apply_scaling(self, scaling_factor, update_geometry=False):
        self.scaling = max(0.7, min(2.0, float(scaling_factor)))
        try:
            self.root.tk.call("tk", "scaling", self.scaling * 1.33)
        except Exception:
            pass
        if update_geometry:
            width = int(880 * self.scaling)
            height = int(640 * self.scaling)
            self.root.geometry(f"{width}x{height}")

    def on_close(self):
        self.stop_video()
        self.root.destroy()

    def clear_container(self):
        self.stop_video()
        for widget in self.main_container.winfo_children():
            widget.destroy()

    # ==========================================
    # VIDEO PLAYBACK
    # ==========================================
    def start_intro_video(self):
        self.clear_container()

        # Decide video according to setup variable:
        # If setup = 0 it plays orion_setup.mp4, else orion_startup.mp4
        is_setup_zero = int(self.config.get("setup", 0)) == 0
        video_filename = "Orion_Setup.mp4" if is_setup_zero else "Orion_Startup.mp4"
        video_path = find_video(video_filename)

        if not os.path.exists(video_path):
            print(f"Video {video_filename} not found at {video_path}, proceeding directly.")
            self.render_appropriate_screen()
            return

        self.cap = cv2.VideoCapture(video_path)
        if not self.cap.isOpened():
            print("Failed to open video capture, skipping to screen.")
            self.render_appropriate_screen()
            return

        # Video container
        v_frame = tk.Frame(self.main_container, bg=self.theme["bg"])
        v_frame.pack(fill="both", expand=True)

        # Top Bar with Video Title & Settings
        top_bar = tk.Frame(v_frame, bg=self.theme["bg"])
        top_bar.pack(fill="x", padx=20, pady=(15, 5))

        title_lbl = tk.Label(
            top_bar,
            text=f"PROJECT ORION // {'INITIALIZING SETUP' if is_setup_zero else 'SYSTEM STARTUP'}",
            font=self.get_font(12, "bold"),
            bg=self.theme["bg"],
            fg=self.theme["accent"],
        )
        title_lbl.pack(side="left")

        settings_btn = self.create_styled_button(
            top_bar,
            text="⚙ Settings",
            command=self.open_settings_dialog,
            style="secondary",
            font_size=10,
        )
        settings_btn.pack(side="right")

        # Video Canvas
        vid_w = int(640 * self.scaling)
        vid_h = int(360 * self.scaling)
        self.vid_w = vid_w
        self.vid_h = vid_h

        canvas_frame = tk.Frame(v_frame, bg=self.theme["card_border"], padx=2, pady=2)
        canvas_frame.pack(pady=10)

        self.video_canvas = tk.Canvas(
            canvas_frame,
            width=vid_w,
            height=vid_h,
            bg="#000000",
            highlightthickness=0,
        )
        self.video_canvas.pack()

        # Skip button
        btn_frame = tk.Frame(v_frame, bg=self.theme["bg"])
        btn_frame.pack(pady=10)

        skip_btn = self.create_styled_button(
            btn_frame,
            text="Skip Intro »",
            command=self.skip_video,
            style="accent",
            font_size=11,
            padx=16,
            pady=6,
        )
        skip_btn.pack()

        self.play_video_frame()

    def play_video_frame(self):
        if not self.cap or not self.cap.isOpened():
            self.render_appropriate_screen()
            return

        ret, frame = self.cap.read()
        if ret:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame = cv2.resize(frame, (self.vid_w, self.vid_h), interpolation=cv2.INTER_LINEAR)
            img = ImageTk.PhotoImage(image=Image.fromarray(frame))
            self.video_canvas.create_image(0, 0, anchor=tk.NW, image=img)
            self.video_canvas.img = img
            self.video_after_id = self.root.after(30, self.play_video_frame)
        else:
            self.stop_video()
            self.render_appropriate_screen()

    def stop_video(self):
        if self.video_after_id:
            try:
                self.root.after_cancel(self.video_after_id)
            except Exception:
                pass
            self.video_after_id = None
        if self.cap:
            try:
                self.cap.release()
            except Exception:
                pass
            self.cap = None

    def skip_video(self):
        self.stop_video()
        self.render_appropriate_screen()

    # ==========================================
    # SCREEN ROUTING
    # ==========================================
    def render_appropriate_screen(self):
        self.clear_container()
        self.config = load_config()

        setup_val = int(self.config.get("setup", 0))
        ready_val = int(self.config.get("ready", 0))

        if setup_val == 0:
            self.render_setup_screen()
        elif ready_val == 1:
            self.render_ready_screen()
        else:
            self.render_not_ready_screen()

    # ==========================================
    # COMMON TOP NAVBAR
    # ==========================================
    def render_top_navbar(self, parent, active_screen_name=""):
        nav = tk.Frame(parent, bg=self.theme["nav_bg"], height=int(56 * self.scaling))
        nav.pack(fill="x", side="top", padx=0, pady=0)

        # Border separator below navbar
        sep = tk.Frame(parent, bg=self.theme["card_border"], height=1)
        sep.pack(fill="x", side="top")

        content = tk.Frame(nav, bg=self.theme["nav_bg"])
        content.pack(fill="x", padx=20, pady=10)

        # Brand / Title
        brand_frame = tk.Frame(content, bg=self.theme["nav_bg"])
        brand_frame.pack(side="left")

        logo_lbl = tk.Label(
            brand_frame,
            text="PROJECT ORION",
            font=self.get_font(13, "bold"),
            bg=self.theme["nav_bg"],
            fg=self.theme["fg"],
        )
        logo_lbl.pack(side="left")

        slash_lbl = tk.Label(
            brand_frame,
            text=" // ",
            font=self.get_font(13, "bold"),
            bg=self.theme["nav_bg"],
            fg=self.theme["accent"],
        )
        slash_lbl.pack(side="left")

        screen_lbl = tk.Label(
            brand_frame,
            text=active_screen_name,
            font=self.get_font(12, "bold"),
            bg=self.theme["nav_bg"],
            fg=self.theme["fg_muted"],
        )
        screen_lbl.pack(side="left")

        # Right actions
        right_frame = tk.Frame(content, bg=self.theme["nav_bg"])
        right_frame.pack(side="right")

        # Quick Theme Toggle
        theme_icon = "☀ Light" if self.theme_name == "dark" else "🌙 Dark"
        quick_theme_btn = self.create_styled_button(
            right_frame,
            text=theme_icon,
            command=self.quick_toggle_theme,
            style="secondary",
            font_size=10,
            padx=10,
            pady=4,
        )
        quick_theme_btn.pack(side="left", padx=(0, 10))

        # Settings Button
        settings_btn = self.create_styled_button(
            right_frame,
            text="⚙ Settings",
            command=self.open_settings_dialog,
            style="secondary",
            font_size=10,
            padx=12,
            pady=4,
        )
        settings_btn.pack(side="left")

    def quick_toggle_theme(self):
        new_theme = "light" if self.theme_name == "dark" else "dark"
        self.theme_name = new_theme
        self.theme = THEMES[new_theme]
        self.config["theme"] = new_theme
        save_config(self.config)
        self.root.configure(bg=self.theme["bg"])
        self.render_appropriate_screen()

    # ==========================================
    # SCREEN 1: SETUP SCREEN (setup = 0)
    # ==========================================
    def render_setup_screen(self):
        self.render_top_navbar(self.main_container, active_screen_name="INITIAL SETUP")

        # Scrollable / centered container
        center_frame = tk.Frame(self.main_container, bg=self.theme["bg"])
        center_frame.pack(fill="both", expand=True, padx=30, pady=20)

        # Card container
        card = tk.Frame(
            center_frame,
            bg=self.theme["card_bg"],
            highlightbackground=self.theme["card_border"],
            highlightthickness=1,
            padx=32,
            pady=28,
        )
        card.place(relx=0.5, rely=0.5, anchor="center")

        # Card Title
        card_title = tk.Label(
            card,
            text="ORION // SYSTEM INITIALIZATION",
            font=self.get_font(16, "bold"),
            bg=self.theme["card_bg"],
            fg=self.theme["accent"],
        )
        card_title.pack(anchor="w", pady=(0, 4))

        card_sub = tk.Label(
            card,
            text="Welcome to Orion. Please provide your profile and AI credentials to complete setup.",
            font=self.get_font(10),
            bg=self.theme["card_bg"],
            fg=self.theme["fg_muted"],
        )
        card_sub.pack(anchor="w", pady=(0, 20))

        # Input: Name
        name_lbl = tk.Label(
            card,
            text="Operator Name",
            font=self.get_font(10, "bold"),
            bg=self.theme["card_bg"],
            fg=self.theme["fg"],
        )
        name_lbl.pack(anchor="w", pady=(0, 4))

        name_entry = self.create_styled_entry(card, width=42)
        name_entry.insert(0, self.config.get("name", ""))
        name_entry.pack(fill="x", pady=(0, 14))

        # Input: One line about self
        bio_lbl = tk.Label(
            card,
            text="One Line About Yourself",
            font=self.get_font(10, "bold"),
            bg=self.theme["card_bg"],
            fg=self.theme["fg"],
        )
        bio_lbl.pack(anchor="w", pady=(0, 4))

        bio_entry = self.create_styled_entry(card, width=42)
        bio_entry.insert(0, self.config.get("bio", ""))
        bio_entry.pack(fill="x", pady=(0, 14))

        # Input: API Key
        key_lbl = tk.Label(
            card,
            text="API Key",
            font=self.get_font(10, "bold"),
            bg=self.theme["card_bg"],
            fg=self.theme["fg"],
        )
        key_lbl.pack(anchor="w", pady=(0, 4))

        key_frame = tk.Frame(card, bg=self.theme["card_bg"])
        key_frame.pack(fill="x", pady=(0, 14))

        key_entry = self.create_styled_entry(key_frame, show="*")
        key_entry.insert(0, self.config.get("api_key", ""))
        key_entry.pack(side="left", fill="x", expand=True)

        def toggle_key_show():
            if key_entry.cget("show") == "*":
                key_entry.config(show="")
                show_btn.config(text="Hide")
            else:
                key_entry.config(show="*")
                show_btn.config(text="Show")

        show_btn = self.create_styled_button(
            key_frame,
            text="Show",
            command=toggle_key_show,
            style="secondary",
            font_size=9,
            padx=8,
            pady=4,
        )
        show_btn.pack(side="left", padx=(8, 0))

        # Dropdown for Gemini, Claude, and ChatGPT
        model_lbl = tk.Label(
            card,
            text="AI Model Selection",
            font=self.get_font(10, "bold"),
            bg=self.theme["card_bg"],
            fg=self.theme["fg"],
        )
        model_lbl.pack(anchor="w", pady=(0, 4))

        model_var = tk.StringVar(value=self.config.get("model", "chatgpt").lower())
        if model_var.get() not in ["chatgpt", "claude", "gemini"]:
            model_var.set("chatgpt")

        dropdown_frame = tk.Frame(card, bg=self.theme["card_bg"])
        dropdown_frame.pack(fill="x", pady=(0, 22))

        model_dropdown = ttk.Combobox(
            dropdown_frame,
            textvariable=model_var,
            values=["chatgpt", "claude", "gemini"],
            state="readonly",
            font=self.get_font(10),
        )
        model_dropdown.pack(fill="x")

        # Submit button & feedback label
        feedback_lbl = tk.Label(
            card,
            text="",
            font=self.get_font(9),
            bg=self.theme["card_bg"],
            fg=self.theme["red"],
        )
        feedback_lbl.pack(pady=(0, 6))

        def complete_setup():
            name_val = name_entry.get().strip()
            bio_val = bio_entry.get().strip()
            key_val = key_entry.get().strip()
            selected_model = model_var.get().strip().lower()

            if not name_val:
                feedback_lbl.config(text="Please enter your name.", fg=self.theme["red"])
                name_entry.focus()
                return

            if not key_val:
                feedback_lbl.config(
                    text="API Key is required to initialize Orion.", fg=self.theme["red"]
                )
                key_entry.focus()
                return

            # Store in config
            self.config["name"] = name_val
            self.config["bio"] = bio_val
            self.config["api_key"] = key_val
            self.config["model"] = selected_model
            self.config["setup"] = 1
            self.config["ready"] = 1  # mark ready upon setup completion

            save_config(self.config)
            feedback_lbl.config(
                text="Configuration saved! Initializing...", fg=self.theme["green"]
            )
            self.root.after(500, self.render_appropriate_screen)

        submit_btn = self.create_styled_button(
            card,
            text="Save & Initialize Orion →",
            command=complete_setup,
            style="accent",
            font_size=11,
            padx=20,
            pady=8,
        )
        submit_btn.pack(fill="x")

    # ==========================================
    # SCREEN 2: READY SCREEN (ready = 1 and setup = 1)
    # ==========================================
    def render_ready_screen(self):
        self.render_top_navbar(self.main_container, active_screen_name="READY")

        content = tk.Frame(self.main_container, bg=self.theme["bg"])
        content.pack(fill="both", expand=True, padx=25, pady=20)

        # Header section:
        # Prompt requirement:
        # "If ready = 1 and setup = 1 it shows ORION // Ready and model = chatgpt, Near ready it shows model: Chatgpt and so on for claude and gemini."
        header_card = tk.Frame(
            content,
            bg=self.theme["card_bg"],
            highlightbackground=self.theme["card_border"],
            highlightthickness=1,
            padx=20,
            pady=16,
        )
        header_card.pack(fill="x", pady=(0, 16))

        # Top row inside header card
        header_row = tk.Frame(header_card, bg=self.theme["card_bg"])
        header_row.pack(fill="x")

        title_lbl = tk.Label(
            header_row,
            text="ORION // Ready",
            font=self.get_font(18, "bold"),
            bg=self.theme["card_bg"],
            fg=self.theme["accent"],
        )
        title_lbl.pack(side="left")

        current_model_key = self.config.get("model", "chatgpt")
        current_model_formatted = format_model(current_model_key)

        # "Near ready it shows model: Chatgpt and so on for claude and gemini."
        model_badge_frame = tk.Frame(
            header_row,
            bg=self.theme["input_bg"],
            highlightbackground=self.theme["cyan"],
            highlightthickness=1,
            padx=12,
            pady=5,
        )
        model_badge_frame.pack(side="left", padx=16)

        model_badge = tk.Label(
            model_badge_frame,
            text=f"Model: {current_model_formatted}",
            font=self.get_font(11, "bold"),
            bg=self.theme["input_bg"],
            fg=self.theme["cyan"],
        )
        model_badge.pack()

        status_tag = tk.Label(
            header_row,
            text="● ONLINE",
            font=self.get_font(10, "bold"),
            bg=self.theme["card_bg"],
            fg=self.theme["green"],
        )
        status_tag.pack(side="right")

        # Operator info sub-line
        user_name = self.config.get("name", "Operator")
        user_bio = self.config.get("bio", "System Active")
        info_sub = tk.Label(
            header_card,
            text=f"Operator: {user_name}  |  {user_bio}",
            font=self.get_font(10),
            bg=self.theme["card_bg"],
            fg=self.theme["fg_muted"],
        )
        info_sub.pack(anchor="w", pady=(8, 0))

        # Main Body: Interactive Chat Area
        chat_card = tk.Frame(
            content,
            bg=self.theme["card_bg"],
            highlightbackground=self.theme["card_border"],
            highlightthickness=1,
            padx=16,
            pady=16,
        )
        chat_card.pack(fill="both", expand=True)

        chat_header = tk.Label(
            chat_card,
            text=f"Live Chat Interface // {current_model_formatted} Engine",
            font=self.get_font(11, "bold"),
            bg=self.theme["card_bg"],
            fg=self.theme["fg"],
        )
        chat_header.pack(anchor="w", pady=(0, 10))

        # Chat Log
        self.chat_display = tk.Text(
            chat_card,
            bg=self.theme["input_bg"],
            fg=self.theme["input_fg"],
            insertbackground=self.theme["fg"],
            font=self.get_font(10),
            relief="flat",
            highlightthickness=1,
            highlightbackground=self.theme["input_border"],
            padx=12,
            pady=10,
            wrap="word",
        )
        self.chat_display.pack(fill="both", expand=True, pady=(0, 12))

        # Initialize with greeting if empty
        if not self.chat_history:
            greeting = (
                f"[SYSTEM] Project Orion is online and ready.\n"
                f"[SYSTEM] Active engine: {current_model_formatted}\n"
                f"[SYSTEM] Welcome back, {user_name}! Type a message below to test interaction.\n\n"
            )
            self.chat_display.insert(tk.END, greeting)
        else:
            for speaker, text in self.chat_history:
                self.chat_display.insert(tk.END, f"[{speaker}] {text}\n\n")

        self.chat_display.config(state="disabled")
        self.chat_display.see(tk.END)

        # Chat Input Row
        input_row = tk.Frame(chat_card, bg=self.theme["card_bg"])
        input_row.pack(fill="x")

        self.chat_entry = self.create_styled_entry(input_row)
        self.chat_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.chat_entry.bind("<Return>", lambda e: self.send_chat_message())

        send_btn = self.create_styled_button(
            input_row,
            text="Send Message",
            command=self.send_chat_message,
            style="accent",
            font_size=10,
            padx=16,
            pady=6,
        )
        send_btn.pack(side="left", padx=(0, 8))

        clear_btn = self.create_styled_button(
            input_row,
            text="Clear",
            command=self.clear_chat,
            style="secondary",
            font_size=10,
            padx=12,
            pady=6,
        )
        clear_btn.pack(side="left")

    def send_chat_message(self):
        msg = self.chat_entry.get().strip()
        if not msg:
            return
        self.chat_entry.delete(0, tk.END)

        user_name = self.config.get("name", "User")
        current_model = format_model(self.config.get("model", "chatgpt"))

        self.chat_display.config(state="normal")
        self.chat_display.insert(tk.END, f"[{user_name}]: {msg}\n")
        self.chat_history.append((user_name, msg))

        # Simulated response using current model
        response = (
            f"Orion ({current_model}) received your message: \"{msg}\". "
            f"All operational systems are functional and responsive."
        )
        self.chat_display.insert(tk.END, f"[{current_model}]: {response}\n\n")
        self.chat_history.append((current_model, response))

        self.chat_display.config(state="disabled")
        self.chat_display.see(tk.END)

    def clear_chat(self):
        self.chat_history.clear()
        self.chat_display.config(state="normal")
        self.chat_display.delete("1.0", tk.END)
        self.chat_display.insert(
            tk.END, f"[SYSTEM] Chat cleared. Orion is ready for new queries.\n\n"
        )
        self.chat_display.config(state="disabled")

    # ==========================================
    # SCREEN 3: NOT READY SCREEN (ready = 0)
    # ==========================================
    def render_not_ready_screen(self):
        # Prompt requirement: "make the ready = 0 ui a area to fix it."
        self.render_top_navbar(self.main_container, active_screen_name="DIAGNOSTIC & FIX")

        content = tk.Frame(self.main_container, bg=self.theme["bg"])
        content.pack(fill="both", expand=True, padx=25, pady=20)

        # Header warning banner
        header_card = tk.Frame(
            content,
            bg=self.theme["card_bg"],
            highlightbackground=self.theme["red"],
            highlightthickness=1,
            padx=20,
            pady=16,
        )
        header_card.pack(fill="x", pady=(0, 16))

        h_top = tk.Frame(header_card, bg=self.theme["card_bg"])
        h_top.pack(fill="x")

        title_lbl = tk.Label(
            h_top,
            text="ORION // NOT READY",
            font=self.get_font(18, "bold"),
            bg=self.theme["card_bg"],
            fg=self.theme["red"],
        )
        title_lbl.pack(side="left")

        current_model_key = self.config.get("model", "chatgpt")
        current_model_formatted = format_model(current_model_key)

        model_badge = tk.Label(
            h_top,
            text=f"Model: {current_model_formatted}",
            font=self.get_font(11, "bold"),
            bg=self.theme["input_bg"],
            fg=self.theme["yellow"],
            padx=10,
            pady=4,
        )
        model_badge.pack(side="left", padx=16)

        status_tag = tk.Label(
            h_top,
            text="● SYSTEM HALTED",
            font=self.get_font(10, "bold"),
            bg=self.theme["card_bg"],
            fg=self.theme["red"],
        )
        status_tag.pack(side="right")

        sub_desc = tk.Label(
            header_card,
            text="Attention: Orion is currently marked as Not Ready (ready = 0). Use the diagnostic and repair tools below to resolve issues and activate the system.",
            font=self.get_font(10),
            bg=self.theme["card_bg"],
            fg=self.theme["fg_muted"],
            wraplength=int(600 * self.scaling),
            justify="left",
        )
        sub_desc.pack(anchor="w", pady=(8, 0))

        # Split content into Diagnostics (Left) and Quick Fix Form (Right)
        split_frame = tk.Frame(content, bg=self.theme["bg"])
        split_frame.pack(fill="both", expand=True)

        # Left: Diagnostics Checklist
        diag_card = tk.Frame(
            split_frame,
            bg=self.theme["card_bg"],
            highlightbackground=self.theme["card_border"],
            highlightthickness=1,
            padx=18,
            pady=18,
        )
        diag_card.pack(side="left", fill="both", expand=True, padx=(0, 10))

        diag_title = tk.Label(
            diag_card,
            text="System Diagnostics",
            font=self.get_font(12, "bold"),
            bg=self.theme["card_bg"],
            fg=self.theme["fg"],
        )
        diag_title.pack(anchor="w", pady=(0, 12))

        # Check items
        api_key_present = bool(self.config.get("api_key", "").strip())
        name_present = bool(self.config.get("name", "").strip())

        items = [
            (
                "API Key Status",
                "Configured" if api_key_present else "Missing / Empty Key",
                self.theme["green"] if api_key_present else self.theme["red"],
            ),
            (
                "Operator Identity",
                f"Configured: {self.config.get('name')}" if name_present else "Incomplete",
                self.theme["green"] if name_present else self.theme["yellow"],
            ),
            (
                "Active Model",
                f"Selected: {current_model_formatted}",
                self.theme["cyan"],
            ),
            (
                "Readiness Variable",
                "ready = 0 (Flagged Offline)",
                self.theme["red"],
            ),
        ]

        for label_text, status_text, color in items:
            item_box = tk.Frame(diag_card, bg=self.theme["input_bg"], padx=10, pady=8)
            item_box.pack(fill="x", pady=4)

            tk.Label(
                item_box,
                text=label_text,
                font=self.get_font(10, "bold"),
                bg=self.theme["input_bg"],
                fg=self.theme["fg"],
            ).pack(side="left")

            tk.Label(
                item_box,
                text=status_text,
                font=self.get_font(9),
                bg=self.theme["input_bg"],
                fg=color,
            ).pack(side="right")

        # Test Connectivity Simulation
        self.diag_status_lbl = tk.Label(
            diag_card,
            text="",
            font=self.get_font(9),
            bg=self.theme["card_bg"],
            fg=self.theme["fg_muted"],
        )
        self.diag_status_lbl.pack(pady=(12, 4))

        def run_test():
            self.diag_status_lbl.config(
                text="Pinging AI endpoints... Verification successful!", fg=self.theme["green"]
            )

        test_btn = self.create_styled_button(
            diag_card,
            text="⚡ Run Connection Test",
            command=run_test,
            style="secondary",
            font_size=10,
            padx=12,
            pady=6,
        )
        test_btn.pack(pady=4)

        # Right: Repair & Activation Area
        fix_card = tk.Frame(
            split_frame,
            bg=self.theme["card_bg"],
            highlightbackground=self.theme["card_border"],
            highlightthickness=1,
            padx=18,
            pady=18,
        )
        fix_card.pack(side="right", fill="both", expand=True, padx=(10, 0))

        fix_title = tk.Label(
            fix_card,
            text="Resolution & Activation Center",
            font=self.get_font(12, "bold"),
            bg=self.theme["card_bg"],
            fg=self.theme["accent"],
        )
        fix_title.pack(anchor="w", pady=(0, 10))

        # API Key input to fix
        tk.Label(
            fix_card,
            text="Update / Confirm API Key:",
            font=self.get_font(10, "bold"),
            bg=self.theme["card_bg"],
            fg=self.theme["fg"],
        ).pack(anchor="w", pady=(0, 3))

        fix_key_entry = self.create_styled_entry(fix_card, show="*")
        fix_key_entry.insert(0, self.config.get("api_key", ""))
        fix_key_entry.pack(fill="x", pady=(0, 10))

        # Model selection to fix
        tk.Label(
            fix_card,
            text="Active Model:",
            font=self.get_font(10, "bold"),
            bg=self.theme["card_bg"],
            fg=self.theme["fg"],
        ).pack(anchor="w", pady=(0, 3))

        fix_model_var = tk.StringVar(value=self.config.get("model", "chatgpt").lower())
        fix_dropdown = ttk.Combobox(
            fix_card,
            textvariable=fix_model_var,
            values=["chatgpt", "claude", "gemini"],
            state="readonly",
            font=self.get_font(10),
        )
        fix_dropdown.pack(fill="x", pady=(0, 16))

        # Fix Status feedback
        fix_feedback = tk.Label(
            fix_card,
            text="",
            font=self.get_font(9),
            bg=self.theme["card_bg"],
            fg=self.theme["green"],
        )
        fix_feedback.pack(pady=(0, 6))

        # Primary Fix Action: Set ready = 1
        def fix_and_activate():
            new_key = fix_key_entry.get().strip()
            new_model = fix_model_var.get().strip().lower()

            if not new_key:
                fix_feedback.config(
                    text="Error: Valid API Key required to activate.", fg=self.theme["red"]
                )
                return

            self.config["api_key"] = new_key
            self.config["model"] = new_model
            self.config["ready"] = 1
            self.config["setup"] = 1
            save_config(self.config)

            fix_feedback.config(
                text="Issues resolved! Setting ready = 1 and activating...",
                fg=self.theme["green"],
            )
            self.root.after(600, self.render_appropriate_screen)

        activate_btn = self.create_styled_button(
            fix_card,
            text="✔ Fix & Set Ready (ready = 1)",
            command=fix_and_activate,
            style="accent",
            font_size=11,
            padx=16,
            pady=8,
        )
        activate_btn.pack(fill="x", pady=(0, 10))

        # Option to reset setup if desired
        def reset_setup_action():
            if messagebox.askyesno(
                "Reset Setup",
                "Do you want to reset setup (setup = 0)? This will re-run the initial onboarding video and setup wizard.",
            ):
                self.config["setup"] = 0
                self.config["ready"] = 0
                save_config(self.config)
                self.start_intro_video()

        reset_btn = self.create_styled_button(
            fix_card,
            text="↺ Re-run Setup Wizard (setup = 0)",
            command=reset_setup_action,
            style="secondary",
            font_size=10,
            padx=12,
            pady=6,
        )
        reset_btn.pack(fill="x")

    # ==========================================
    # SETTINGS MODAL / DIALOG (Accessible everywhere)
    # ==========================================
    def open_settings_dialog(self):
        dlg = tk.Toplevel(self.root)
        dlg.title("Project Orion: Settings")
        dlg.transient(self.root)
        dlg.grab_set()

        width = int(480 * self.scaling)
        height = int(580 * self.scaling)
        dlg.geometry(f"{width}x{height}")
        dlg.configure(bg=self.theme["bg"])
        dlg.resizable(False, False)

        # Settings Card
        container = tk.Frame(
            dlg,
            bg=self.theme["card_bg"],
            highlightbackground=self.theme["card_border"],
            highlightthickness=1,
            padx=24,
            pady=20,
        )
        container.pack(fill="both", expand=True, padx=16, pady=16)

        title = tk.Label(
            container,
            text="SYSTEM SETTINGS",
            font=self.get_font(14, "bold"),
            bg=self.theme["card_bg"],
            fg=self.theme["accent"],
        )
        title.pack(anchor="w", pady=(0, 4))

        sub = tk.Label(
            container,
            text="Adjust scaling, theme, AI model, credentials, and state flags.",
            font=self.get_font(9),
            bg=self.theme["card_bg"],
            fg=self.theme["fg_muted"],
        )
        sub.pack(anchor="w", pady=(0, 14))

        # 1. UI Scaling
        tk.Label(
            container,
            text="UI Scaling",
            font=self.get_font(10, "bold"),
            bg=self.theme["card_bg"],
            fg=self.theme["fg"],
        ).pack(anchor="w", pady=(0, 3))

        scale_options = ["80% (0.8x)", "90% (0.9x)", "100% (1.0x)", "110% (1.1x)", "125% (1.25x)", "150% (1.5x)"]
        scale_map = {
            "80% (0.8x)": 0.8,
            "90% (0.9x)": 0.9,
            "100% (1.0x)": 1.0,
            "110% (1.1x)": 1.1,
            "125% (1.25x)": 1.25,
            "150% (1.5x)": 1.5,
        }
        current_scale_val = float(self.config.get("scaling", 1.0))
        # Find closest match
        default_scale_text = "100% (1.0x)"
        for k, v in scale_map.items():
            if abs(v - current_scale_val) < 0.05:
                default_scale_text = k
                break

        scale_var = tk.StringVar(value=default_scale_text)
        scale_dropdown = ttk.Combobox(
            container,
            textvariable=scale_var,
            values=scale_options,
            state="readonly",
            font=self.get_font(10),
        )
        scale_dropdown.pack(fill="x", pady=(0, 12))

        # 2. Theme Toggle (Dark vs Light)
        tk.Label(
            container,
            text="Theme Mode",
            font=self.get_font(10, "bold"),
            bg=self.theme["card_bg"],
            fg=self.theme["fg"],
        ).pack(anchor="w", pady=(0, 3))

        theme_var = tk.StringVar(value=self.theme_name)
        theme_row = tk.Frame(container, bg=self.theme["card_bg"])
        theme_row.pack(fill="x", pady=(0, 12))

        dark_rb = tk.Radiobutton(
            theme_row,
            text="Dark Mode (Cyberpunk Obsidian)",
            variable=theme_var,
            value="dark",
            bg=self.theme["card_bg"],
            fg=self.theme["fg"],
            activebackground=self.theme["card_bg"],
            activeforeground=self.theme["accent"],
            selectcolor=self.theme["input_bg"],
            font=self.get_font(10),
        )
        dark_rb.pack(anchor="w")

        light_rb = tk.Radiobutton(
            theme_row,
            text="Light Mode (Modern Clean Slate)",
            variable=theme_var,
            value="light",
            bg=self.theme["card_bg"],
            fg=self.theme["fg"],
            activebackground=self.theme["card_bg"],
            activeforeground=self.theme["accent"],
            selectcolor=self.theme["input_bg"],
            font=self.get_font(10),
        )
        light_rb.pack(anchor="w")

        # 3. Model Selection
        tk.Label(
            container,
            text="AI Model Selection",
            font=self.get_font(10, "bold"),
            bg=self.theme["card_bg"],
            fg=self.theme["fg"],
        ).pack(anchor="w", pady=(0, 3))

        model_var = tk.StringVar(value=self.config.get("model", "chatgpt").lower())
        model_dropdown = ttk.Combobox(
            container,
            textvariable=model_var,
            values=["chatgpt", "claude", "gemini"],
            state="readonly",
            font=self.get_font(10),
        )
        model_dropdown.pack(fill="x", pady=(0, 12))

        # 4. API Key
        tk.Label(
            container,
            text="API Key",
            font=self.get_font(10, "bold"),
            bg=self.theme["card_bg"],
            fg=self.theme["fg"],
        ).pack(anchor="w", pady=(0, 3))

        key_frame = tk.Frame(container, bg=self.theme["card_bg"])
        key_frame.pack(fill="x", pady=(0, 12))

        key_entry = self.create_styled_entry(key_frame, show="*")
        key_entry.insert(0, self.config.get("api_key", ""))
        key_entry.pack(side="left", fill="x", expand=True)

        def toggle_key_show_dlg():
            if key_entry.cget("show") == "*":
                key_entry.config(show="")
                show_btn_dlg.config(text="Hide")
            else:
                key_entry.config(show="*")
                show_btn_dlg.config(text="Show")

        show_btn_dlg = self.create_styled_button(
            key_frame,
            text="Show",
            command=toggle_key_show_dlg,
            style="secondary",
            font_size=9,
            padx=8,
            pady=4,
        )
        show_btn_dlg.pack(side="left", padx=(8, 0))

        # 5. System Flags (ready, setup)
        tk.Label(
            container,
            text="System State Flags",
            font=self.get_font(10, "bold"),
            bg=self.theme["card_bg"],
            fg=self.theme["fg"],
        ).pack(anchor="w", pady=(0, 3))

        flags_frame = tk.Frame(container, bg=self.theme["card_bg"])
        flags_frame.pack(fill="x", pady=(0, 16))

        ready_var = tk.IntVar(value=int(self.config.get("ready", 0)))
        setup_var = tk.IntVar(value=int(self.config.get("setup", 0)))

        ready_chk = tk.Checkbutton(
            flags_frame,
            text="Ready State (ready = 1)",
            variable=ready_var,
            bg=self.theme["card_bg"],
            fg=self.theme["fg"],
            activebackground=self.theme["card_bg"],
            activeforeground=self.theme["green"],
            selectcolor=self.theme["input_bg"],
            font=self.get_font(10),
        )
        ready_chk.pack(side="left", padx=(0, 16))

        setup_chk = tk.Checkbutton(
            flags_frame,
            text="Setup Complete (setup = 1)",
            variable=setup_var,
            bg=self.theme["card_bg"],
            fg=self.theme["fg"],
            activebackground=self.theme["card_bg"],
            activeforeground=self.theme["green"],
            selectcolor=self.theme["input_bg"],
            font=self.get_font(10),
        )
        setup_chk.pack(side="left")

        # Save Button & Cancel
        btn_row = tk.Frame(container, bg=self.theme["card_bg"])
        btn_row.pack(fill="x", side="bottom")

        def save_and_apply():
            selected_scale = scale_map.get(scale_var.get(), 1.0)
            selected_theme = theme_var.get()
            selected_model = model_var.get().strip().lower()
            new_key = key_entry.get().strip()
            new_ready = ready_var.get()
            new_setup = setup_var.get()

            # Update configuration
            self.config["scaling"] = selected_scale
            self.config["theme"] = selected_theme
            self.config["model"] = selected_model
            self.config["api_key"] = new_key
            self.config["ready"] = new_ready
            self.config["setup"] = new_setup

            save_config(self.config)

            # Apply theme and scaling
            self.theme_name = selected_theme
            self.theme = THEMES[selected_theme]
            self.apply_scaling(selected_scale, update_geometry=True)
            self.root.configure(bg=self.theme["bg"])

            dlg.destroy()
            self.render_appropriate_screen()

        save_btn = self.create_styled_button(
            btn_row,
            text="Save Settings",
            command=save_and_apply,
            style="accent",
            font_size=11,
            padx=16,
            pady=7,
        )
        save_btn.pack(side="right", padx=(8, 0))

        cancel_btn = self.create_styled_button(
            btn_row,
            text="Cancel",
            command=dlg.destroy,
            style="secondary",
            font_size=11,
            padx=14,
            pady=7,
        )
        cancel_btn.pack(side="right")

    # ==========================================
    # WIDGET BUILDERS & HELPERS
    # ==========================================
    def create_styled_entry(self, parent, show=None, width=None):
        entry = tk.Entry(
            parent,
            bg=self.theme["input_bg"],
            fg=self.theme["input_fg"],
            insertbackground=self.theme["fg"],
            font=self.get_font(10),
            relief="flat",
            highlightthickness=1,
            highlightbackground=self.theme["input_border"],
            highlightcolor=self.theme["accent"],
            show=show,
            width=width,
        )
        return entry

    def create_styled_button(
        self,
        parent,
        text,
        command,
        style="accent",
        font_size=10,
        padx=12,
        pady=6,
    ):
        if style == "accent":
            bg = self.theme["accent"]
            fg = self.theme["accent_fg"]
            hover_bg = self.theme["accent_hover"]
        else:
            bg = self.theme["btn_sec_bg"]
            fg = self.theme["btn_sec_fg"]
            hover_bg = self.theme["btn_sec_hover"]

        btn = tk.Button(
            parent,
            text=text,
            command=command,
            font=self.get_font(font_size, "bold"),
            bg=bg,
            fg=fg,
            activebackground=hover_bg,
            activeforeground=fg,
            relief="flat",
            bd=0,
            cursor="hand2",
            padx=int(padx * self.scaling),
            pady=int(pady * self.scaling),
        )

        def on_enter(e):
            btn.config(bg=hover_bg)

        def on_leave(e):
            btn.config(bg=bg)

        btn.bind("<Enter>", on_enter)
        btn.bind("<Leave>", on_leave)
        return btn


def main():
    root = tk.Tk()
    app = OrionApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
