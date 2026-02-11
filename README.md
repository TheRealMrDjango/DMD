# 🗑️ DMD - Discord Message Deleter

![Python](https://img.shields.io/badge/Python-3.x-blue?style=for-the-badge&logo=python)
![Windows](https://img.shields.io/badge/Platform-Windows-0078D6?style=for-the-badge&logo=windows)
![macOS](https://img.shields.io/badge/Platform-macOS-000000?style=for-the-badge&logo=apple)
![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)

**DMD (Discord Message Deleter)** is a user-friendly automation tool designed to help you bulk delete messages from Discord channels and DMs. Featuring a modern GUI, this tool automates the process of fetching and deleting message history while intelligently handling rate limits.

---

## 🔒 Secure by Design: RAM-Only Operation

**Your privacy is paramount.** DMD is engineered to operate exclusively in **RAM-Only Mode**, ensuring your data remains secure on your own machine.

* **🚫 No Disk Writes:** Your authentication tokens and fetched message data are **never** written to your hard drive. There are no config files or cache folders to clean up.
* **⚡ Instant Wipe:** As soon as you close the application, all sensitive data is instantly vanished from memory.
* **🛡️ Local Execution:** Everything runs 100% locally on your computer. No data is ever sent to third-party servers.

---

## ⚠️ IMPORTANT SECURITY WARNING

> **PLEASE READ:**
> While this tool is secure locally, it requires your personal Discord authorization headers to function.
>
> 1.  **NEVER SHARE YOUR FETCH COMMAND:** The text you paste contains your **Auth Token**. Sharing this gives others full access to your account.
> 2.  **USE RESPONSIBLY:** Automating user accounts is technically against Discord Terms of Service. Use this tool at your own risk and in moderation.

---

## 📥 Download & Run (No Python Required)

We provide standalone executables for Windows and macOS so you don't need to install Python.

### 🪟 Windows Users
1.  Go to the **[Releases]([https://will-include-link](https://github.com/TheRealMrDjango/DMD/releases/download/v.0.2.5.1/DMD-0.2.5.1.zip))** page.
2.  Download `DMD.exe`.
3.  Run the application directly.

---

## 🚀 Key Features

* **🖥️ Modern GUI:** Built with `CustomTkinter` for a clean, dark-mode-friendly user interface.
* **🔄 Auto-Looping Logic:** Automatically cycles through fetching, parsing, and deleting until the channel is empty.
* **⏱️ Smart Rate-Limiting:** Includes random sleep timers (5-8 seconds) and automatic back-off for HTTP 429 (Rate Limit) errors to simulate human behavior.
* **🛑 Real-time Logs:** Monitor the deletion progress directly inside the app window.

---

## ⚙️ How to Use

### Step 1: Get Your Fetch Command
1.  Open **Discord** in a web browser (Chrome, Edge, Firefox).
2.  Navigate to the channel or DM you want to clean.
3.  Open **Developer Tools** (Press `F12` or `Ctrl+Shift+I`).
4.  Go to the **Network** tab.
5.  Scroll up in the chat to trigger a message load. Look for a request named `messages?limit=50`.
6.  **Right-Click** that request -> **Copy** -> **Copy as fetch**.

### Step 2: Start Cleaning
1.  Paste the **Fetch Command** into the text box in the DMD app.
2.  Click **Start Cleaning**.
3.  The tool will process the deletion loop until the messages are gone.

### Step 3: Finish
* Simply close the app. Since it runs in RAM, no files are left behind!

---

## 🐍 Run from Source (Developers)

If you prefer to run the raw Python script:

1.  **Install Requirements:**
    ```bash
    pip install -r requirements.txt
    ```
2.  **Run the GUI:**
    ```bash
    python gui.py
    ```

---

## 📂 Project Structure

* `gui.py`: The main entry point. Handles the UI, threading, and coordinates the secure memory flow.
* `get_messages.py`: Parses the `fetch` command and retrieves message history directly into memory.
* `delete_message.py`: Takes the list of messages from memory and sends individual DELETE requests.

---

## 📝 Disclaimer


*This software is for educational purposes only. The developer is not responsible for any account bans or data loss resulting from the use of this tool. Please use responsibly.*
