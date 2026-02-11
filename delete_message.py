import requests
import json
import re
import ast
import time
import random


class MessageDeleter:
    def __init__(self, messages_data, fetch_content=None, headers=None):
        self.raw_data = messages_data
        self.fetch_content = fetch_content
        self.headers = headers or {}
        self.messages_to_delete = []

    def run(self):
        print("--- Starting Message Deletion Process ---")

        # If headers weren't passed in, try to extract them from the fetch string
        if not self.headers and self.fetch_content:
            self._parse_fetch_headers()
        
        if not self.headers:
            print("Error: No authentication headers found.")
            return

        self._load_messages_from_memory()
        self._process_deletions()

    def _parse_fetch_headers(self):
        """Parses headers and auth token from the provided fetch string."""
        if not self.fetch_content:
            print("Error: No fetch content provided.")
            return False

        content = self.fetch_content

        start_index = content.find('{')
        end_index = content.rfind('}')

        if start_index == -1 or end_index == -1:
            print("Error: Could not find config object in fetch command.")
            return False

        config_str = content[start_index: end_index + 1]
        config_str = re.sub(r'\bnull\b', 'None', config_str)
        config_str = re.sub(r'\btrue\b', 'True', config_str)
        config_str = re.sub(r'\bfalse\b', 'False', config_str)
        config_str = re.sub(r'(?m)^\s*([a-zA-Z_]\w*)\s*:', r'"\1":', config_str)

        try:
            options = ast.literal_eval(config_str)
            self.headers = options.get('headers', {})
            return True
        except Exception as e:
            print(f"Error parsing fetch headers: {e}")
            return False

    def _load_messages_from_memory(self):
        """Flattens the message data structure."""
        if not self.raw_data:
            print("No data provided to deleter.")
            return

        # Support both flat lists and nested lists (from pagination)
        # Discord API usually returns a list of messages directly, or a dict with "messages" key
        if isinstance(self.raw_data, dict):
            raw_messages = self.raw_data.get('messages', [])
        elif isinstance(self.raw_data, list):
            raw_messages = self.raw_data
        else:
            raw_messages = []

        self.messages_to_delete = []

        for item in raw_messages:
            if isinstance(item, list):
                self.messages_to_delete.extend(item)
            else:
                self.messages_to_delete.append(item)

        print(f"Found {len(self.messages_to_delete)} messages to delete.")

    def _process_deletions(self):
        """Loops through messages and sends DELETE requests."""
        total = len(self.messages_to_delete)

        for index, msg in enumerate(self.messages_to_delete):
            try:
                message_id = msg.get('id')
                channel_id = msg.get('channel_id')
                content = msg.get('content', '[No Content]')

                if not message_id or not channel_id:
                    print(f"Skipping item {index}: Missing ID or Channel ID")
                    continue

                url = f"https://discord.com/api/v9/channels/{channel_id}/messages/{message_id}"

                print(f"[{index + 1}/{total}] Deleting: {content[:50]}...")

                response = requests.delete(url, headers=self.headers)

                if response.status_code in [200, 204]:
                    print("   -> Success")
                elif response.status_code == 429:
                    print("   -> Rate Limited! Sleeping extra.")
                    time.sleep(5)
                else:
                    print(f"   -> Failed: {response.status_code} - {response.text}")

                # Random sleep
                sleep_time = random.uniform(5, 8)
                print(f"   -> Sleeping for {sleep_time:.2f} seconds...")
                time.sleep(sleep_time)

            except Exception as e:
                print(f"Error processing message {index}: {e}")