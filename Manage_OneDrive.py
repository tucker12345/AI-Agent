# Databricks notebook source
# MAGIC %pip install msal requests

# COMMAND ----------

# DBTITLE 1,Widget setup
# Create widget only if it doesn't exist (preserves %run parameter)
try:
    # Try to read existing widget (from %run parameter)
    skip_tests = dbutils.widgets.get("skip_tests") == "true"
except Exception:
    # Widget doesn't exist, create with default
    dbutils.widgets.text("skip_tests", "true", "Skip Tests")
    skip_tests = True

# COMMAND ----------

import msal
import requests
from IPython.display import display, HTML

# COMMAND ----------

# import msal
# import requests
# from IPython.display import display, HTML

# # For PERSONAL OneDrive, you need a different app registration:
# # 1. Go to https://portal.azure.com/#blade/Microsoft_AAD_RegisteredApps/ApplicationsListBlade
# # 2. New registration:
# #    - Name: "Databricks OneDrive Access"
# #    - Supported account types: "Personal Microsoft accounts only"
# #    - Redirect URI: Leave blank for device code flow
# # 3. After creation, copy the Application (client) ID
# # 4. No client secret needed for device code flow

# PERSONAL_CLIENT_ID = "277a0c97-691d-4f16-a6ac-1df892794f8f"  # Replace with your app ID for personal accounts

# # Device Code Flow for Personal Microsoft Accounts
# def get_personal_onedrive_token():
#     authority = "https://login.microsoftonline.com/consumers"  # For personal accounts
#     app = msal.PublicClientApplication(
#         PERSONAL_CLIENT_ID,
#         authority=authority
#     )
    
#     # Scopes for OneDrive access
#     # Note: offline_access is automatically included by MSAL - don't pass it explicitly
#     scopes = ["Files.ReadWrite.All"]
    
#     # Start device code flow
#     flow = app.initiate_device_flow(scopes=scopes)
    
#     if "user_code" not in flow:
#         raise Exception(f"Failed to create device flow: {flow}")
    
#     # Display the code and URL to the user
#     display(HTML(f'''
#     <div style="background-color: #fff3cd; border: 2px solid #ffc107; padding: 20px; border-radius: 5px; margin: 10px 0;">
#         <h3 style="color: #856404; margin-top: 0;">🔐 Sign in to your Personal OneDrive</h3>
#         <ol style="color: #856404; font-size: 14px;">
#             <li>Visit: <a href="{flow['verification_uri']}" target="_blank" style="color: #0066cc; font-weight: bold;">{flow['verification_uri']}</a></li>
#             <li>Enter this code: <strong style="font-size: 18px; color: #d9534f;">{flow['user_code']}</strong></li>
#             <li>Sign in with your Microsoft account (tkoike_uw@yahoo.ca)</li>
#         </ol>
#         <p style="color: #856404; margin-bottom: 0;">⏱️ Code expires in {flow['expires_in'] // 60} minutes. Waiting for you to complete sign-in...</p>
#     </div>
#     '''))
    
#     # Wait for the user to authenticate
#     result = app.acquire_token_by_device_flow(flow)
    
#     if "access_token" in result:
#         print("✅ Successfully authenticated!")
#         return result["access_token"]
#     else:
#         raise Exception(f"Authentication failed: {result.get('error_description')}")

# # List files in personal OneDrive
# def list_personal_onedrive_files(access_token):
#     headers = {
#         "Authorization": f"Bearer {access_token}",
#         "Content-Type": "application/json"
#     }
    
#     # For personal accounts, use /me endpoint (this works with delegated auth)
#     response = requests.get(
#         "https://graph.microsoft.com/v1.0/me/drive/root/children",
#         headers=headers
#     )
    
#     if response.status_code == 200:
#         files = response.json()
#         return files["value"]
#     else:
#         raise Exception(f"Error listing files: {response.status_code} - {response.text}")

# if PERSONAL_CLIENT_ID == "your-app-client-id":
#     print("⚠️ Please create an Azure app for PERSONAL Microsoft accounts and update PERSONAL_CLIENT_ID")
#     print("See comments above for instructions")
# else:
#     # Get token using device code flow
#     token = get_personal_onedrive_token()
    
#     # List files
#     files = list_personal_onedrive_files(token)
#     print(f"\n📁 Found {len(files)} files/folders in your OneDrive:\n")
#     for file in files:
#         print(f"  - {file['name']} ({file.get('size', 0)} bytes)")

# COMMAND ----------

# DBTITLE 1,Class-based OneDrive Client
class PersonalOneDriveClient:
    @staticmethod
    def get_personal_onedrive_token(client_id):
        authority = "https://login.microsoftonline.com/consumers"  # For personal accounts
        app = msal.PublicClientApplication(
            client_id,
            authority=authority
        )
        
        # Scopes for OneDrive access
        # Note: offline_access is automatically included by MSAL - don't pass it explicitly
        scopes = ["Files.ReadWrite.All"]
        
        # Start device code flow
        flow = app.initiate_device_flow(scopes=scopes)
        
        if "user_code" not in flow:
            raise Exception(f"Failed to create device flow: {flow}")
        
        # Display the code and URL to the user
        display(HTML(f'''
        <div style="background-color: #fff3cd; border: 2px solid #ffc107; padding: 20px; border-radius: 5px; margin: 10px 0;">
            <h3 style="color: #856404; margin-top: 0;">🔐 Sign in to your Personal OneDrive</h3>
            <ol style="color: #856404; font-size: 14px;">
                <li>Visit: <a href="{flow['verification_uri']}" target="_blank" style="color: #0066cc; font-weight: bold;">{flow['verification_uri']}</a></li>
                <li>Enter this code: <strong style="font-size: 18px; color: #d9534f;">{flow['user_code']}</strong></li>
                <li>Sign in with your Microsoft account (tkoike_uw@yahoo.ca)</li>
            </ol>
            <p style="color: #856404; margin-bottom: 0;">⏱️ Code expires in {flow['expires_in'] // 60} minutes. Waiting for you to complete sign-in...</p>
        </div>
        '''))
        
        # Wait for the user to authenticate
        result = app.acquire_token_by_device_flow(flow)
        
        if "access_token" in result:
            print("✅ Successfully authenticated!")
            return result["access_token"]
        else:
            raise Exception(f"Authentication failed: {result.get('error_description')}")
    
    @staticmethod
    def list_personal_onedrive_files(access_token):
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        # For personal accounts, use /me endpoint (this works with delegated auth)
        response = requests.get(
            "https://graph.microsoft.com/v1.0/me/drive/root/children",
            headers=headers
        )
        
        if response.status_code == 200:
            files = response.json()
            return files["value"]
        else:
            raise Exception(f"Error listing files: {response.status_code} - {response.text}")

# COMMAND ----------

# DBTITLE 1,Internal Test (only runs when executed directly)
# Test code - only runs when this notebook is executed directly

PERSONAL_CLIENT_ID = "277a0c97-691d-4f16-a6ac-1df892794f8f" 

if not skip_tests:
    if PERSONAL_CLIENT_ID == "your-app-client-id":
        print("⚠️ Please create an Azure app for PERSONAL Microsoft accounts and update PERSONAL_CLIENT_ID")
        print("See comments above for instructions")
    else:
        # Get token using device code flow (using class static method)
        token = PersonalOneDriveClient.get_personal_onedrive_token(PERSONAL_CLIENT_ID)
        
        # List files (using class static method)
        files = PersonalOneDriveClient.list_personal_onedrive_files(token)
        print(f"\n📁 Found {len(files)} files/folders in your OneDrive:\n")
        for file in files:
            print(f"  - {file['name']} ({file.get('size', 0)} bytes)")

# COMMAND ----------

# import requests
# import os

# # Navigate to a specific folder and list files
# def get_folder_contents(access_token, folder_path):
#     """
#     Get contents of a specific folder in OneDrive
#     folder_path: e.g., '/AI/RAG/mineral'
#     """
#     headers = {
#         "Authorization": f"Bearer {access_token}",
#         "Content-Type": "application/json"
#     }
    
#     # Use the path-based API to access specific folders
#     # Remove leading slash if present for the API call
#     clean_path = folder_path.strip('/')
    
#     response = requests.get(
#         f"https://graph.microsoft.com/v1.0/me/drive/root:/{clean_path}:/children",
#         headers=headers
#     )
    
#     if response.status_code == 200:
#         items = response.json()
#         return items.get("value", [])
#     else:
#         raise Exception(f"Error accessing folder: {response.status_code} - {response.text}")

# # Download a file from OneDrive
# def download_onedrive_file(access_token, item_id, local_path):
#     """
#     Download a file from OneDrive by item ID
#     """
#     headers = {"Authorization": f"Bearer {access_token}"}
    
#     response = requests.get(
#         f"https://graph.microsoft.com/v1.0/me/drive/items/{item_id}/content",
#         headers=headers
#     )
   
#     if response.status_code == 200:
#         # Ensure directory exists
#         os.makedirs(os.path.dirname(local_path), exist_ok=True)
        
#         with open(local_path, "wb") as f:
#             f.write(response.content)
#         print(f"✅ Downloaded: {local_path}")
#         return local_path
#     else:
#         raise Exception(f"Error downloading file: {response.status_code} - {response.text}")

# # Access the mineral folder
# target_folder = "/AI/RAG/mineral"

# try:
#     # Use the token from the previous cell
#     # If you need to re-authenticate, run cell 5 again
#     items = get_folder_contents(token, target_folder)
    
#     print(f"📁 Contents of '{target_folder}' ({len(items)} items):\n")
    
#     files = []
#     folders = []
    
#     for item in items:
#         if 'folder' in item:
#             folders.append(item)
#             print(f"  📂 {item['name']}/")
#         else:
#             files.append(item)
#             size_mb = item.get('size', 0) / (1024 * 1024)
#             print(f"  📄 {item['name']} ({size_mb:.2f} MB)")
    
#     print(f"\n📊 Summary: {len(folders)} folders, {len(files)} files")
    
#     # Store items for potential download
#     mineral_items = items
    
# except Exception as e:
#     print(f"❌ Error: {e}")
#     print("\n💡 Tip: If you see an authentication error, run Cell 5 again to get a fresh token.")

# COMMAND ----------

# DBTITLE 1,OneDrive Upload Manager Class
import requests
import os

class OneDriveUploadManager:

    # Navigate to a specific folder and list files
    @staticmethod
    def get_folder_contents(access_token, folder_path):
        """
        Get contents of a specific folder in OneDrive
        folder_path: e.g., '/AI/RAG/mineral'
        """
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        # Use the path-based API to access specific folders
        # Remove leading slash if present for the API call
        clean_path = folder_path.strip('/')
        
        response = requests.get(
            f"https://graph.microsoft.com/v1.0/me/drive/root:/{clean_path}:/children",
            headers=headers
        )
        
        if response.status_code == 200:
            items = response.json()
            return items.get("value", [])
        else:
            raise Exception(f"Error accessing folder: {response.status_code} - {response.text}")


    # Download a file from OneDrive
    @staticmethod
    def download_onedrive_file(access_token, item_id, local_path):
        """
        Download a file from OneDrive by item ID
        """
        headers = {"Authorization": f"Bearer {access_token}"}
        
        response = requests.get(
            f"https://graph.microsoft.com/v1.0/me/drive/items/{item_id}/content",
            headers=headers
        )
    
        if response.status_code == 200:
            # Ensure directory exists
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            
            with open(local_path, "wb") as f:
                f.write(response.content)
            print(f"✅ Downloaded: {local_path}")
            return local_path
        else:
            raise Exception(f"Error downloading file: {response.status_code} - {response.text}")


    # @staticmethod
    # def upload_file_to_onedrive(access_token, local_file_path, onedrive_path):
    #     """
    #     Upload a single file to OneDrive
    #     local_file_path: Path to the local file
    #     onedrive_path: Target path in OneDrive (e.g., '/AI/RAG/mineral/file.txt')
    #     """
    #     headers = {
    #         "Authorization": f"Bearer {access_token}",
    #         "Content-Type": "application/octet-stream"
    #     }
        
    #     # Clean the path
    #     clean_path = onedrive_path.strip('/')
        
    #     # Read the file content
    #     with open(local_file_path, "rb") as f:
    #         file_content = f.read()
        
    #     # Upload using PUT to the path-based API
    #     response = requests.put(
    #         f"https://graph.microsoft.com/v1.0/me/drive/root:/{clean_path}:/content",
    #         headers=headers,
    #         data=file_content
    #     )
        
    #     if response.status_code in [200, 201]:
    #         return response.json()
    #     else:
    #         raise Exception(f"Error uploading file: {response.status_code} - {response.text}")
    
    # @staticmethod
    # def upload_folder(access_token, local_folder_path, onedrive_folder_path):
    #     """
    #     Recursively upload a local folder to OneDrive
    #     local_folder_path: Path to the local folder (e.g., '/tmp/RAG/vector_store')
    #     onedrive_folder_path: Target path in OneDrive (e.g., '/AI/RAG/mineral/vector_store')
    #     """
    #     import os
        
    #     uploaded_files = []
        
    #     # Walk through all files and subdirectories
    #     for root, dirs, files in os.walk(local_folder_path):
    #         for filename in files:
    #             # Get the full local path
    #             local_file = os.path.join(root, filename)
                
    #             # Calculate the relative path from the source folder
    #             rel_path = os.path.relpath(local_file, local_folder_path)
                
    #             # Construct the OneDrive path
    #             onedrive_file_path = f"{onedrive_folder_path}/{rel_path}".replace("\\", "/")
                
    #             try:
    #                 OneDriveUploadManager.upload_file_to_onedrive(access_token, local_file, onedrive_file_path)
    #                 uploaded_files.append(rel_path)
    #                 print(f"✅ Uploaded: {rel_path}")
    #             except Exception as e:
    #                 print(f"❌ Failed to upload {rel_path}: {e}")
        
    #     print(f"\n📊 Upload complete: {len(uploaded_files)} files uploaded to {onedrive_folder_path}")
    #     return len(uploaded_files)

# COMMAND ----------

# DBTITLE 1,Internal Test (folder contents listing)
# Test code - only runs when this notebook is executed directly
if not skip_tests:
    # Access the mineral folder
    target_folder = "/AI/RAG/mineral"
    
    try:
        # Use the token from the previous cell
        # If you need to re-authenticate, run cell 5 again
        items = get_folder_contents(token, target_folder)
        
        print(f"📁 Contents of '{target_folder}' ({len(items)} items):\n")
        
        files = []
        folders = []
        
        for item in items:
            if 'folder' in item:
                folders.append(item)
                print(f"  📂 {item['name']}/")
            else:
                files.append(item)
                size_mb = item.get('size', 0) / (1024 * 1024)
                print(f"  📄 {item['name']} ({size_mb:.2f} MB)")
        
        print(f"\n📊 Summary: {len(folders)} folders, {len(files)} files")
        
        # Store items for potential download
        mineral_items = items
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("\n💡 Tip: If you see an authentication error, run Cell 5 again to get a fresh token.")


# COMMAND ----------

# def save_and_upload_nodes(final_nodes, token, onedrive_output_folder, local_output_dir):
#     import os
#     import json

#     # Ensure local output directory exists
#     os.makedirs(local_output_dir, exist_ok=True)

#     # Save each node as a .json file locally
#     for i, node in enumerate(final_nodes):
#         node_file = os.path.join(local_output_dir, f"node_{i+1}.json")
#         with open(node_file, "w") as f:
#             json.dump({
#                 "content": node.get_content(),
#                 "metadata": node.metadata
#             }, f, ensure_ascii=False, indent=2)

#     # Upload each .json file to OneDrive
#     for filename in os.listdir(local_output_dir):
#         if filename.endswith(".json"):
#             local_file_path = os.path.join(local_output_dir, filename)
#             dbutils.notebook.run(
#                 "Manage_OneDrive", 60, {
#                     "method": "upload_file_to_onedrive",
#                     "token": token,
#                     "src_path": local_file_path,
#                     "dst_path": f"{onedrive_output_folder}/{filename}"
#                 }
#             )
#             print(f"Uploaded: {filename} to OneDrive folder {onedrive_output_folder}")

# COMMAND ----------

# DBTITLE 1,OneDrive Node Manager Class
class OneDriveNodeManager:
    @staticmethod
    def save_and_upload_nodes(final_nodes, token, onedrive_output_folder, local_output_dir):
        """
        Save nodes as JSON files locally and upload them to OneDrive
        final_nodes: List of node objects with get_content() and metadata
        token: OneDrive access token
        onedrive_output_folder: Target folder path in OneDrive
        local_output_dir: Local directory to save JSON files temporarily
        """
        import os
        import json

        # Ensure local output directory exists
        os.makedirs(local_output_dir, exist_ok=True)

        # Save each node as a .json file locally
        for i, node in enumerate(final_nodes):
            node_file = os.path.join(local_output_dir, f"node_{i+1}.json")
            with open(node_file, "w") as f:
                json.dump({
                    "content": node.get_content(),
                    "metadata": node.metadata
                }, f, ensure_ascii=False, indent=2)

        # Upload each .json file to OneDrive using OneDriveUploadManager
        uploaded_count = 0
        for filename in os.listdir(local_output_dir):
            if filename.endswith(".json"):
                local_file_path = os.path.join(local_output_dir, filename)
                onedrive_file_path = f"{onedrive_output_folder}/{filename}"
                
                try:
                    OneDriveFileManager.upload_file_to_onedrive(token, local_file_path, onedrive_file_path)
                    uploaded_count += 1
                    print(f"✅ Uploaded: {filename} to {onedrive_output_folder}")
                except Exception as e:
                    print(f"❌ Failed to upload {filename}: {e}")
        
        print(f"\n📊 Upload complete: {uploaded_count} files uploaded to {onedrive_output_folder}")
        return uploaded_count

# COMMAND ----------

# DBTITLE 1,Upload folder to OneDrive
# def upload_file_to_onedrive(access_token, local_file_path, onedrive_path):
#     """
#     Upload a single file to OneDrive
#     local_file_path: Path to the local file
#     onedrive_path: Target path in OneDrive (e.g., '/AI/RAG/mineral/file.txt')
#     """
#     headers = {
#         "Authorization": f"Bearer {access_token}",
#         "Content-Type": "application/octet-stream"
#     }
    
#     # Clean the path
#     clean_path = onedrive_path.strip('/')
    
#     # Read the file content
#     with open(local_file_path, "rb") as f:
#         file_content = f.read()
    
#     # Upload using PUT to the path-based API
#     response = requests.put(
#         f"https://graph.microsoft.com/v1.0/me/drive/root:/{clean_path}:/content",
#         headers=headers,
#         data=file_content
#     )
    
#     if response.status_code in [200, 201]:
#         return response.json()
#     else:
#         raise Exception(f"Error uploading file: {response.status_code} - {response.text}")

# def upload_folder(access_token, local_folder_path, onedrive_folder_path):
#     """
#     Recursively upload a local folder to OneDrive
#     local_folder_path: Path to the local folder (e.g., '/tmp/RAG/vector_store')
#     onedrive_folder_path: Target path in OneDrive (e.g., '/AI/RAG/mineral/vector_store')
#     """
#     import os
    
#     uploaded_files = []
    
#     # Walk through all files and subdirectories
#     for root, dirs, files in os.walk(local_folder_path):
#         for filename in files:
#             # Get the full local path
#             local_file = os.path.join(root, filename)
            
#             # Calculate the relative path from the source folder
#             rel_path = os.path.relpath(local_file, local_folder_path)
            
#             # Construct the OneDrive path
#             onedrive_file_path = f"{onedrive_folder_path}/{rel_path}".replace("\\", "/")
            
#             try:
#                 upload_file_to_onedrive(access_token, local_file, onedrive_file_path)
#                 uploaded_files.append(rel_path)
#                 print(f"✅ Uploaded: {rel_path}")
#             except Exception as e:
#                 print(f"❌ Failed to upload {rel_path}: {e}")
    
#     print(f"\n📊 Upload complete: {len(uploaded_files)} files uploaded to {onedrive_folder_path}")
#     return len(uploaded_files)

# COMMAND ----------

# DBTITLE 1,OneDrive File Manager Class
class OneDriveFileManager:
    @staticmethod
    def upload_file_to_onedrive(access_token, local_file_path, onedrive_path):
        """
        Upload a single file to OneDrive
        local_file_path: Path to the local file
        onedrive_path: Target path in OneDrive (e.g., '/AI/RAG/mineral/file.txt')
        """
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/octet-stream"
        }
        
        # Clean the path
        clean_path = onedrive_path.strip('/')
        
        # Read the file content
        with open(local_file_path, "rb") as f:
            file_content = f.read()
        
        # Upload using PUT to the path-based API
        response = requests.put(
            f"https://graph.microsoft.com/v1.0/me/drive/root:/{clean_path}:/content",
            headers=headers,
            data=file_content
        )
        
        if response.status_code in [200, 201]:
            return response.json()
        else:
            raise Exception(f"Error uploading file: {response.status_code} - {response.text}")
    
    @staticmethod
    def upload_folder(access_token, local_folder_path, onedrive_folder_path):
        """
        Recursively upload a local folder to OneDrive
        local_folder_path: Path to the local folder (e.g., '/tmp/RAG/vector_store')
        onedrive_folder_path: Target path in OneDrive (e.g., '/AI/RAG/mineral/vector_store')
        """
        import os
        
        uploaded_files = []
        
        # Walk through all files and subdirectories
        for root, dirs, files in os.walk(local_folder_path):
            for filename in files:
                # Get the full local path
                local_file = os.path.join(root, filename)
                
                # Calculate the relative path from the source folder
                rel_path = os.path.relpath(local_file, local_folder_path)
                
                # Construct the OneDrive path
                onedrive_file_path = f"{onedrive_folder_path}/{rel_path}".replace("\\", "/")
                
                try:
                    OneDriveFileManager.upload_file_to_onedrive(access_token, local_file, onedrive_file_path)
                    uploaded_files.append(rel_path)
                    print(f"✅ Uploaded: {rel_path}")
                except Exception as e:
                    print(f"❌ Failed to upload {rel_path}: {e}")
        
        print(f"\n📊 Upload complete: {len(uploaded_files)} files uploaded to {onedrive_folder_path}")
        return len(uploaded_files)

# COMMAND ----------

# DBTITLE 1,Method dispatcher
# # Method dispatcher for dbutils.notebook.run calls
# method = dbutils.widgets.get("method")

# if method == "get_personal_onedrive_token":
#     token = get_personal_onedrive_token()
#     dbutils.notebook.exit(token)

# elif method == "get_folder_contents":
#     token = dbutils.widgets.get("token")
#     folder_path = dbutils.widgets.get("folder_path")
#     items = get_folder_contents(token, folder_path)
#     dbutils.notebook.exit(items)

# elif method == "download_onedrive_file":
#     token = dbutils.widgets.get("token")
#     item_id = dbutils.widgets.get("item_id")
#     dst_path = dbutils.widgets.get("dst_path")
#     result = download_onedrive_file(token, item_id, dst_path)
#     dbutils.notebook.exit(result)

# elif method == "upload_file_to_onedrive":
#     token = dbutils.widgets.get("token")
#     src_path = dbutils.widgets.get("src_path")
#     dst_path = dbutils.widgets.get("dst_path")
#     result = upload_file_to_onedrive(token, src_path, dst_path)
#     dbutils.notebook.exit(str(result))

# elif method == "upload_folder":
#     token = dbutils.widgets.get("token")
#     src_path = dbutils.widgets.get("src_path")
#     dst_path = dbutils.widgets.get("dst_path")
#     count = upload_folder(token, src_path, dst_path)
#     dbutils.notebook.exit(str(count))

# elif method == "save_and_upload_nodes":
#     import json
#     nodes = json.loads(dbutils.widgets.get("nodes"))
#     token = dbutils.widgets.get("token")
#     onedrive_output_folder = dbutils.widgets.get("onedrive_output_folder")
#     local_output_dir = dbutils.widgets.get("local_output_dir")
#     save_and_upload_nodes(nodes, token, onedrive_output_folder, local_output_dir)
#     dbutils.notebook.exit("success")

# else:
#     dbutils.notebook.exit(f"Unknown method: {method}")