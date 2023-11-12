import sys
import os
current_script_path = os.path.abspath(__file__)
project_root_path = os.path.abspath(os.path.join(current_script_path, '..', '..', 'src'))
sys.path.append(project_root_path)