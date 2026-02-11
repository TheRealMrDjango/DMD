import requests
import json
import re
import ast

class FetchRunner:
    def __init__(self, fetch_content=None, url=None, headers=None):
        self.fetch_content = fetch_content
        self.url = url
        self.headers = headers
        self.options = {'headers': headers} if headers else {}

    def run(self):
        # If we weren't given a URL/Headers, try to parse the fetch string
        if not self.url or not self.headers:
            if not self.fetch_content:
                print("Error: No data or fetch content provided.")
                return None
            if not self._parse_fetch_command(self.fetch_content):
                return None
        
        return self._execute_request()

    def _parse_fetch_command(self, content):
        """Extracts the URL and configuration options from the JS fetch command."""
        # 1. Extract URL
        url_match = re.search(r"fetch\(['\"](.*?)['\"]", content)
        if not url_match:
            print("Error: Could not find a URL in the fetch command.")
            return False
        self.url = url_match.group(1)

        # 2. Extract Config Object
        start_index = content.find('{')
        end_index = content.rfind('}')

        if start_index == -1 or end_index == -1:
            # No config means simple GET
            self.options = {'method': 'GET', 'headers': {}}
            return True

        config_str = content[start_index: end_index + 1]

        # 3. Clean JS Syntax
        config_str = re.sub(r'\bnull\b', 'None', config_str)
        config_str = re.sub(r'\btrue\b', 'True', config_str)
        config_str = re.sub(r'\bfalse\b', 'False', config_str)

        # 4. Fix Unquoted Keys
        config_str = re.sub(r'(?m)^\s*([a-zA-Z_]\w*)\s*:', r'"\1":', config_str)

        # 5. Parse to Dictionary
        try:
            self.options = ast.literal_eval(config_str)
            return True
        except Exception as e:
            print(f"Error parsing config: {e}")
            return False

    def _execute_request(self):
        """Executes the HTTP request using the parsed options."""
        method = self.options.get('method', 'GET')
        headers = self.options.get('headers', {})
        body_raw = self.options.get('body')

        json_payload = None
        if isinstance(body_raw, str):
            try:
                json_payload = json.loads(body_raw)
                body_raw = None
            except:
                pass

        print(f"Running {method} request to: {self.url}...")

        try:
            response = requests.request(
                method=method,
                url=self.url,
                headers=headers,
                data=body_raw,
                json=json_payload
            )
            print(f"Status Code: {response.status_code}")

            if response.status_code == 200:
                try:
                    return response.json()
                except json.JSONDecodeError:
                    print("Response was not valid JSON.")
                    return None
            else:
                print(f"Request failed with status: {response.status_code}")
                return None

        except Exception as e:
            print(f"Request execution failed: {e}")
            return None