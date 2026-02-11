from js_control_tools.autofetchserver import AuthHeaderSniffer
import customtkinter as ctk
import tkinter as tk
import threading
import sys
import queue
import time
import asyncio

# --- Import Backend Logic ---
from get_messages import FetchRunner
from delete_message import MessageDeleter

# --- Global Configuration ---
ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

class TextRedirector:
    """Redirects print statements to the GUI log window."""
    def __init__(self, q):
        self.q = q
    def write(self, string):
        self.q.put(string)
    def flush(self):
        pass

class DiscordCleanerApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.ahs = None
        self.auth_value = None
        self.auto_selected_channel = None

        self.title("DMD - Discord Message Deleter")
        self.geometry("700x700")

        self.running = False
        self.log_queue = queue.Queue()

        # --- GUI Layout ---
        self.input_frame = ctk.CTkFrame(self)
        self.input_frame.pack(side="top", fill="x", padx=20, pady=(20, 10))

        self.lbl_instruction = ctk.CTkLabel(self.input_frame, text="Manual Mode: Paste Discord 'fetch' command here:", font=("Roboto", 14, "bold"))
        self.lbl_instruction.pack(anchor="w", padx=10, pady=(10, 5))

        self.txt_fetch = ctk.CTkTextbox(self.input_frame, height=120, font=("Consolas", 12))
        self.txt_fetch.pack(fill="x", padx=10, pady=(0, 10))

        self.control_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.control_frame.pack(side="top", fill="x", padx=20, pady=10)

        self.btn_start = ctk.CTkButton(self.control_frame, text="Start Cleaning", command=self.start_process,
                                       fg_color="#2CC985", hover_color="#229A66", font=("Roboto", 15, "bold"), height=50)
        self.btn_start.pack(fill="x", padx=0, pady=5)

        self.btn_auto_fetch = ctk.CTkButton(self.control_frame, text="Auto Fetch via Chrome", command=self.launch_sniffer_thread,
                                           fg_color="#3B8ED0", hover_color="#36719F", font=("Roboto", 15, "bold"), height=50)
        self.btn_auto_fetch.pack(fill="x", padx=0, pady=5)

        self.auto_fetch_status = ctk.CTkLabel(self, text="Auto-Fetch: Idle", text_color="gray", font=("Roboto", 12))
        self.auto_fetch_status.pack(side="top", pady=2)

        self.lbl_status = ctk.CTkLabel(self, text="Status: Idle", text_color="gray", font=("Roboto", 12))
        self.lbl_status.pack(side="top", pady=5)

        self.log_frame = ctk.CTkFrame(self)
        self.log_frame.pack(side="top", fill="both", expand=True, padx=20, pady=(10, 20))

        self.log_area = ctk.CTkTextbox(self.log_frame, state='disabled', font=("Consolas", 11))
        self.log_area.pack(fill="both", expand=True, padx=10, pady=10)

        self.update_logs()

    def update_logs(self):
        try:
            while True:
                msg = self.log_queue.get_nowait()
                self.log_area.configure(state='normal')
                self.log_area.insert("end", msg)
                self.log_area.see("end")
                self.log_area.configure(state='disabled')
        except queue.Empty:
            pass
        self.after(100, self.update_logs)

    def launch_sniffer_thread(self):
        """Starts the sniffer in a background thread."""
        self.btn_auto_fetch.configure(state="disabled", text="Sniffing...")
        threading.Thread(target=self.start_webbrowser_tool, daemon=True).start()

    def start_webbrowser_tool(self):
        def on_find(rurl, hname, hvalue):
            if str(rurl) == "https://discord.com/api/v9/users/@me" and str(hname).lower() == "authorization":
                self.auth_value = str(hvalue)
                # Thread-safe UI update
                self.after(0, lambda: self.auto_fetch_status.configure(text="Auth Captured! Now click a channel.", text_color="#2CC985"))

        self.ahs = AuthHeaderSniffer("https://discord.com/channels/@me", on_found=on_find)
        asyncio.run(self.ahs.start())

    def start_process(self):
        if self.running: return

        # Update channel ID if using sniffer
        if self.ahs:
            self.auto_selected_channel = self.ahs.get_current_channel()

        fetch_content = self.txt_fetch.get("0.0", "end").strip()
        
        # Validation Logic
        has_auto = bool(self.auth_value and self.auto_selected_channel)
        has_manual = bool(fetch_content and "fetch" in fetch_content)

        if not has_auto and not has_manual:
            tk.messagebox.showerror("Error", "Please provide a 'fetch' command OR use Auto Fetch.")
            return

        self.running = True
        self.btn_start.configure(state="disabled", text="Running...")
        self.lbl_status.configure(text="Status: Running...", text_color="#2CC985")

        threading.Thread(target=self.run_logic_loop, args=(fetch_content,), daemon=True).start()

    def run_logic_loop(self, fetch_content):
        original_stdout = sys.stdout
        sys.stdout = TextRedirector(self.log_queue)

        try:
            print("--- Starting Process ---")
            
            # Determine Mode
            use_dynamic = bool(self.auth_value and self.auto_selected_channel)
            
            if use_dynamic:
                # Ensure channel ID is a string, not a list/tuple
                chan_id = self.auto_selected_channel[1] if isinstance(self.auto_selected_channel, (list, tuple)) else self.auto_selected_channel
                print(f"MODE: Auto-Fetch | Channel: {chan_id}")
                d_url = f"https://discord.com/api/v9/channels/{chan_id}/messages?limit=100"
                d_headers = {"authorization": self.auth_value}
            else:
                print("MODE: Manual (String Parsing)")

            batch = 1
            while True:
                print(f"\n[Batch {batch}] Fetching...")
                
                if use_dynamic:
                    fetcher = FetchRunner(url=d_url, headers=d_headers)
                else:
                    fetcher = FetchRunner(fetch_content=fetch_content)

                messages = fetcher.run()
                
                # Check message count
                msg_list = messages if isinstance(messages, list) else messages.get('messages', []) if isinstance(messages, dict) else []
                count = len(msg_list)

                if count == 0:
                    print("No more messages found. Channel is clean!")
                    break

                print(f"Found {count} messages. Cooling down (5s)...")
                time.sleep(5)

                print(f"Deleting {count} messages...")
                if use_dynamic:
                    deleter = MessageDeleter(messages_data=messages, headers=d_headers)
                else:
                    deleter = MessageDeleter(messages_data=messages, fetch_content=fetch_content)
                deleter.run()

                batch += 1
                time.sleep(2)

        except Exception as e:
            print(f"Loop Error: {e}")
        finally:
            sys.stdout = original_stdout
            self.running = False
            self.after(0, self._reset_ui_state)

    def _reset_ui_state(self):
        self.btn_start.configure(state="normal", text="Start Cleaning")
        self.lbl_status.configure(text="Status: Idle", text_color="gray")
        print("--- Process Finished ---")

if __name__ == "__main__":
    app = DiscordCleanerApp()
    app.mainloop()