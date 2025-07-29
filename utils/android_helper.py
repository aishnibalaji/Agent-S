"""
helper utilities for working with Android environments
"""
from android_env import AndroidEnv
from typing import Dict, Any, Optional
import numpy as np
from PIL import Image

class AndroidHelper:
    
    @staticmethod
    def create_environment(task_name: str = "settings_wifi") -> AndroidEnv:
        """
        creates and initializes the Android environment
        """
        try:
            env = AndroidEnv(
                task_name=task_name,
                device_type='pixel_4',  #pixel 4 device type but you are able to change this
                show_touches=True,  # visual feedback
                show_pointer_location=True 
            )
            
            # reset environment to initial state
            observation = env.reset()
            
            print(f"Environment created successfully!")
            print(f"Screen size: {observation['pixels'].shape}")
            
            return env
            
        except Exception as e:
            print(f"Error creating environment: {e}")
            print("Make sure you have android_world installed and configured properly")
            raise
    
    @staticmethod
    def capture_screenshot(env: AndroidEnv) -> Image.Image:
        """Captures and returns the current screen as a PIL Image"""
        obs = env.observe()
        pixels = obs.get('pixels', None)
        
        if pixels is not None:
            # convert numpy array to PIL image
            return Image.fromarray(pixels.astype('uint8'))
        return None
    
    @staticmethod
    def parse_ui_tree(ui_tree: Dict, max_depth: int = 10) -> List[Dict]:
        """
        flattens the UI tree into a list of elements with their properties for easier search purposes
        """
        elements = []
        
        def traverse(node, depth=0):
            if depth > max_depth:
                return
                
            # extract element info
            element = {
                'depth': depth,
                'class': node.get('class', ''),
                'text': node.get('text', ''),
                'content_desc': node.get('content-desc', ''),
                'resource_id': node.get('resource-id', ''),
                'bounds': node.get('bounds', []),
                'clickable': node.get('clickable', False),
                'scrollable': node.get('scrollable', False)
            }
            
            # only adds elements with an identifiable property
            if any([element['text'], element['content_desc'], element['resource_id']]):
                elements.append(element)
            
            for child in node.get('children', []):
                traverse(child, depth + 1)
        
        traverse(ui_tree)
        return elements
    
    @staticmethod
    def find_element_by_text(ui_tree: Dict, text: str, partial_match: bool = True) -> Optional[Dict]:
        """
        finds an element in the UI tree using its text content
        """
        elements = AndroidHelper.parse_ui_tree(ui_tree)
        text_lower = text.lower()
        
        for element in elements:
            element_text = element['text'].lower()
            element_desc = element['content_desc'].lower()
            
            if partial_match:
                if text_lower in element_text or text_lower in element_desc:
                    return element
            else:
                if text_lower == element_text or text_lower == element_desc:
                    return element
        
        return None