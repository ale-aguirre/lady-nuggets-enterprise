import websocket # NOTE: pip install websocket-client
import uuid
import json
import urllib.request
import urllib.parse
import random
import os
import time

class ComfyClient:
    def __init__(self, server_address="127.0.0.1:8188"):
        self.server_address = server_address
        self.client_id = str(uuid.uuid4())
        self.ws = None

    def connect(self):
        """Establishes websocket connection"""
        try:
            self.ws = websocket.WebSocket()
            self.ws.connect(f"ws://{self.server_address}/ws?clientId={self.client_id}")
            print(f"✅ Connected to ComfyUI at {self.server_address}")
            return True
        except Exception as e:
            print(f"❌ Failed to connect to ComfyUI: {e}")
            return False

    def queue_prompt(self, prompt_workflow):
        """Sends the workflow (JSON) to the queue"""
        p = {"prompt": prompt_workflow, "client_id": self.client_id}
        data = json.dumps(p).encode('utf-8')
        req = urllib.request.Request(f"http://{self.server_address}/prompt", data=data)
        return json.loads(urllib.request.urlopen(req).read())

    def get_image(self, filename, subfolder, folder_type):
        """Downloads the generated image"""
        data = {"filename": filename, "subfolder": subfolder, "type": folder_type}
        url_values = urllib.parse.urlencode(data)
        with urllib.request.urlopen(f"http://{self.server_address}/view?{url_values}") as response:
            return response.read()

    def get_history(self, prompt_id):
        """Gets execution history for a prompt ID"""
        with urllib.request.urlopen(f"http://{self.server_address}/history/{prompt_id}") as response:
            return json.loads(response.read())

    def generate(self, workflow_path, prompt_text, negative_prompt="", seed=None, output_dir="output"):
        """
        Main generation function.
        1. Loads workflow JSON.
        2. Injects prompts and seed.
        3. Queues job.
        4. Waits for result.
        5. Downloads image.
        """
        if not self.ws and not self.connect():
            return None

        if not os.path.exists(workflow_path):
            print(f"❌ Workflow not found: {workflow_path}")
            return None
            
        with open(workflow_path, 'r', encoding='utf-8') as f:
            workflow = json.load(f)

        # === INJECTION MAGIC ===
        # We need to find the KSampler, CLIP Text Encode, etc.
        # This is heuristics-based since node IDs change.
        # Ideally, we tag nodes in ComfyUI, but for raw JSON we iterate types.
        
        if seed is None:
            seed = random.randint(1, 1000000000000)

        loader_node = None
        pos_node = None
        neg_node = None
        seed_node = None
        
        for node_id, node in workflow.items():
            class_type = node.get("class_type", "")
            inputs = node.get("inputs", {})
            
            # Find KSampler (for seed)
            if "KSampler" in class_type or "Sampler" in class_type:
                if "seed" in inputs:
                    inputs["seed"] = seed
                    # Also set random generation to 'fixed' to ensure our seed works
                    # inputs["control_after_generate"] = "fixed" 
                    seed_node = node_id

            # Find Prompts (CLIPTextEncode)
            # Heuristic: Positive usually connects to KSampler 'positive', Negative to 'negative'
            # But simpler: check text content placeholders if they exist, OR
            # Just look for the boxes. 
            # FOR NOW: We assume the user has put "POSITIVE_PROMPT" and "NEGATIVE_PROMPT" 
            # strings in the workflow JSON as placeholders.
            if "CLIPTextEncode" in class_type:
                text_val = inputs.get("text", "")
                if isinstance(text_val, str):
                    if "POSITIVE_PROMPT" in text_val or text_val == "":
                        inputs["text"] = prompt_text
                        pos_node = node_id
                    elif "NEGATIVE_PROMPT" in text_val:
                        inputs["text"] = negative_prompt
                        neg_node = node_id

        # Send to Queue
        print(f"🚀 Queuing Prompt (Seed: {seed})...")
        prompt_res = self.queue_prompt(workflow)
        prompt_id = prompt_res['prompt_id']
        
        # Wait for completion via WebSocket
        while True:
            out = self.ws.recv()
            if isinstance(out, str):
                message = json.loads(out)
                if message['type'] == 'executing':
                    data = message['data']
                    if data['node'] is None and data['prompt_id'] == prompt_id:
                        print("✨ Generation Complete!")
                        break # Execution done
            else:
                continue # Binary data (previews)

        # Get Result Filename from History
        history = self.get_history(prompt_id)[prompt_id]
        outputs = history['outputs']
        
        generated_files = []
        for node_id in outputs:
            node_output = outputs[node_id]
            if 'images' in node_output:
                for image in node_output['images']:
                    filename = image['filename']
                    subfolder = image['subfolder']
                    folder_type = image['type']
                    
                    print(f"📥 Downloading {filename}...")
                    image_data = self.get_image(filename, subfolder, folder_type)
                    
                    if not os.path.exists(output_dir):
                        os.makedirs(output_dir)
                        
                    out_path = os.path.join(output_dir, f"comfy_{seed}_{filename}")
                    with open(out_path, 'wb') as f:
                        f.write(image_data)
                    generated_files.append(out_path)
                    
        return generated_files
