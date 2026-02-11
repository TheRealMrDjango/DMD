import customtkinter as ctk
import tkinter as tk
import threading
import sys
import queue
import time
import os
import json

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

        self.title("DMD")
        self.geometry("700x700")

        self.running = False
        self.log_queue = queue.Queue()

        # --- GUI Layout ---

        # 1. Input Section
        self.input_frame = ctk.CTkFrame(self)
        self.input_frame.pack(side="top", fill="x", padx=20, pady=(20, 10))

        self.lbl_instruction = ctk.CTkLabel(self.input_frame, text="Paste your Discord 'fetch' command here:",
                                            font=("Roboto", 14, "bold"))
        self.lbl_instruction.pack(anchor="w", padx=10, pady=(10, 5))

        self.txt_fetch = ctk.CTkTextbox(self.input_frame, height=120, font=("Consolas", 12))
        self.txt_fetch.pack(fill="x", padx=10, pady=(0, 10))

        # 2. Control Section
        self.control_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.control_frame.pack(side="top", fill="x", padx=20, pady=10)

        self.btn_start = ctk.CTkButton(self.control_frame, text="Start Cleaning", command=self.start_process,
                                       fg_color="#2CC985", hover_color="#229A66", font=("Roboto", 15, "bold"),
                                       height=50)
        self.btn_start.pack(fill="x", padx=0)

        self.lbl_status = ctk.CTkLabel(self, text="Status: Idle", text_color="gray", font=("Roboto", 12))
        self.lbl_status.pack(side="top", pady=5)

        # 3. Log Section
        self.log_frame = ctk.CTkFrame(self)
        self.log_frame.pack(side="top", fill="both", expand=True, padx=20, pady=(10, 20))

        self.lbl_logs = ctk.CTkLabel(self.log_frame, text="Process Logs:", font=("Roboto", 12, "bold"))
        self.lbl_logs.pack(anchor="w", padx=10, pady=(5, 0))

        self.log_area = ctk.CTkTextbox(self.log_frame, state='disabled', font=("Consolas", 11),
                                       activate_scrollbars=True)
        self.log_area.pack(fill="both", expand=True, padx=10, pady=5)

        # 4. Footer
        self.footer_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.footer_frame.pack(side="bottom", fill="x", padx=20, pady=10)

        self.btn_clear = ctk.CTkButton(self.footer_frame, text="Clear Logs", command=self.clear_logs,
                                       fg_color="transparent", border_width=2, text_color=("gray10", "#DCE4EE"))
        self.btn_clear.pack(side="right")

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

    def clear_logs(self):
        self.log_area.configure(state='normal')
        self.log_area.delete("0.0", "end")
        self.log_area.configure(state='disabled')

    def start_process(self):
        if self.running: return

        fetch_content = self.txt_fetch.get("0.0", "end").strip()
        if not fetch_content or "fetch" not in fetch_content:
            tk.messagebox.showerror("Error", "Please paste a valid fetch command.")
            return

        self.running = True
        self.btn_start.configure(state="disabled", text="Running...")
        self.txt_fetch.configure(state="disabled")
        self.lbl_status.configure(text="Status: Running...", text_color="#2CC985")

        # Run in separate thread
        threading.Thread(target=self.run_logic_loop, args=(fetch_content,), daemon=True).start()

    def run_logic_loop(self, fetch_content):
        original_stdout = sys.stdout
        sys.stdout = TextRedirector(self.log_queue)

        try:
            print("--- Initializing (Fully RAM Secure) ---")

            batch_count = 1

            while True:
                print(f"\n=== STARTING BATCH {batch_count} ===")

                print("1. Fetching messages...")
                fetcher = FetchRunner(fetch_content=fetch_content)

                # Capture data directly in variable
                messages_data = fetcher.run()

                if not messages_data:
                    # If None (error) or empty list
                    print("   -> No messages found or error occurred. Stopping.")
                    break

                # Calculate count based on structure
                count = 0
                if isinstance(messages_data, list):
                    count = len(messages_data)
                elif isinstance(messages_data, dict):
                    count = len(messages_data.get('messages', []))

                print(f"   -> Found {count} messages.")

                if count == 0:
                    print("   -> Channel clean! Stopping.")
                    break

                print("2. Sleeping 10s...")
                time.sleep(10)

                print(f"3. Deleting {count} messages...")
                # Pass both the Auth string AND the message data to deleter
                deleter = MessageDeleter(fetch_content=fetch_content, messages_data=messages_data)
                deleter.run()

                print("   -> Restarting in 2s...")
                batch_count += 1
                time.sleep(2)

        except Exception as e:
            print(f"\nERROR: {e}")
            import traceback
            traceback.print_exc()
        finally:
            sys.stdout = original_stdout
            self.running = False
            self.after(0, self._reset_ui_state)

    def _reset_ui_state(self):
        self.btn_start.configure(state="normal", text="Start Cleaning")
        self.txt_fetch.configure(state="normal")
        self.lbl_status.configure(text="Status: Finished / Idle", text_color="gray")
        print("\n=== Process Finished ===")


if __name__ == "__main__":
    app = DiscordCleanerApp()
    app.mainloop()