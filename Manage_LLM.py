# Databricks notebook source
# DBTITLE 1,Cell 1
# MAGIC %uv pip install torch transformers accelerate
# MAGIC # dbutils.library.restartPython()

# COMMAND ----------

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

# DBTITLE 1,Verify packages
# Verify torch and transformers are installed
# import torch
# import transformers

# print(f"✅ PyTorch version: {torch.__version__}")
# print(f"✅ Transformers version: {transformers.__version__}")

if not skip_tests:
    import torch
    import transformers
    print(f"✅ PyTorch version: {torch.__version__}")
    print(f"✅ Transformers version: {transformers.__version__}")

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

# DBTITLE 1,Cell 5
# import torch  # Import torch first to ensure it's available
# from transformers import AutoModelForCausalLM, AutoTokenizer
# import os
# import requests


# # Function to upload a file to OneDrive
# def upload_to_onedrive(access_token, local_file_path, onedrive_folder_path, file_name):
#     """
#     Upload a file to OneDrive
#     Uses simple PUT for files < 4MB, resumable upload session for larger files
#     onedrive_folder_path: e.g., '/AI/RAG/models'
#     """
#     file_size = os.path.getsize(local_file_path)
#     clean_path = onedrive_folder_path.strip('/')
    
#     # For small files (<4MB), use simple PUT
#     if file_size < 4 * 1024 * 1024:
#         headers = {
#             "Authorization": f"Bearer {access_token}",
#             "Content-Type": "application/octet-stream"
#         }
        
#         with open(local_file_path, 'rb') as f:
#             file_content = f.read()
        
#         response = requests.put(
#             f"https://graph.microsoft.com/v1.0/me/drive/root:/{clean_path}/{file_name}:/content",
#             headers=headers,
#             data=file_content
#         )
        
#         if response.status_code in [200, 201]:
#             print(f"✅ Uploaded: {file_name}")
#             return True
#         else:
#             print(f"❌ Error uploading {file_name}: {response.status_code} - {response.text}")
#             return False
    
#     # For large files (>=4MB), use resumable upload session
#     else:
#         print(f"   Using resumable upload (file size: {file_size / (1024*1024):.2f} MB)...")
        
#         # Step 1: Create upload session
#         headers = {
#             "Authorization": f"Bearer {access_token}",
#             "Content-Type": "application/json"
#         }
        
#         session_response = requests.post(
#             f"https://graph.microsoft.com/v1.0/me/drive/root:/{clean_path}/{file_name}:/createUploadSession",
#             headers=headers,
#             json={"item": {"@microsoft.graph.conflictBehavior": "replace"}}
#         )
        
#         if session_response.status_code not in [200, 201]:
#             print(f"❌ Error creating upload session: {session_response.status_code} - {session_response.text}")
#             return False
        
#         upload_url = session_response.json()["uploadUrl"]
        
#         # Step 2: Upload file in chunks (10MB chunks)
#         chunk_size = 10 * 1024 * 1024  # 10MB chunks
        
#         with open(local_file_path, 'rb') as f:
#             chunk_number = 0
#             while True:
#                 chunk = f.read(chunk_size)
#                 if not chunk:
#                     break
                
#                 start = chunk_number * chunk_size
#                 end = start + len(chunk) - 1
                
#                 chunk_headers = {
#                     "Content-Length": str(len(chunk)),
#                     "Content-Range": f"bytes {start}-{end}/{file_size}"
#                 }
                
#                 chunk_response = requests.put(
#                     upload_url,
#                     headers=chunk_headers,
#                     data=chunk
#                 )
                
#                 if chunk_response.status_code not in [200, 201, 202]:
#                     print(f"❌ Error uploading chunk {chunk_number}: {chunk_response.status_code}")
#                     return False
                
#                 chunk_number += 1
#                 progress = min(100, (end + 1) * 100 / file_size)
#                 print(f"   Progress: {progress:.1f}%", end='\r')
        
#         print(f"\n✅ Uploaded: {file_name}")
#         return True

# # Define paths
# model_name = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"
# local_model_dir = "/tmp/RAG/saved_model"
# onedrive_model_path = "/AI/RAG/models/TinyLlama"

# # Create local directory
# os.makedirs(local_model_dir, exist_ok=True)

# print(f"📦 Downloading and saving model: {model_name}")
# print("This may take a few minutes...\n")

# # Load and save the model and tokenizer
# try:
#     # Load tokenizer and model
#     tokenizer = AutoTokenizer.from_pretrained(model_name)
#     model = AutoModelForCausalLM.from_pretrained(
#         model_name,
#         device_map="cpu",
#         torch_dtype="auto"
#     )
    
#     # Save to local directory
#     print(f"💾 Saving model to {local_model_dir}...")
#     tokenizer.save_pretrained(local_model_dir)
#     model.save_pretrained(local_model_dir)
#     print(f"✅ Model saved locally\n")
    
#     # Upload to OneDrive
#     print(f"☁️ Uploading model files to OneDrive: {onedrive_model_path}\n")
    
#     uploaded_count = 0
#     failed_count = 0
    
#     for file_name in os.listdir(local_model_dir):
#         file_path = os.path.join(local_model_dir, file_name)
#         if os.path.isfile(file_path):
#             file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
#             print(f"Uploading {file_name} ({file_size_mb:.2f} MB)...")
            
#             if upload_to_onedrive(token, file_path, onedrive_model_path, file_name):
#                 uploaded_count += 1
#             else:
#                 failed_count += 1
    
#     print(f"\n📊 Upload Summary:")
#     print(f"  ✅ Successful: {uploaded_count} files")
#     print(f"  ❌ Failed: {failed_count} files")
#     print(f"\n🎉 Model persisted to OneDrive: {onedrive_model_path}")
    
# except Exception as e:
#     print(f"❌ Error: {e}")
#     print("\n💡 Tip: If you see an authentication error, run Cell 6 again to refresh the token.")

# COMMAND ----------

# DBTITLE 1,OneDriveManager class
import os
import requests

class LLMManager:
    """Manager class for OneDrive operations"""
    
    @staticmethod
    def upload_to_onedrive(access_token, local_file_path, onedrive_folder_path, file_name):
        """
        Upload a file to OneDrive
        Uses simple PUT for files < 4MB, resumable upload session for larger files
        onedrive_folder_path: e.g., '/AI/RAG/models'
        """
        file_size = os.path.getsize(local_file_path)
        clean_path = onedrive_folder_path.strip('/')
        
        # For small files (<4MB), use simple PUT
        if file_size < 4 * 1024 * 1024:
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/octet-stream"
            }
            
            with open(local_file_path, 'rb') as f:
                file_content = f.read()
            
            response = requests.put(
                f"https://graph.microsoft.com/v1.0/me/drive/root:/{clean_path}/{file_name}:/content",
                headers=headers,
                data=file_content
            )
            
            if response.status_code in [200, 201]:
                print(f"✅ Uploaded: {file_name}")
                return True
            else:
                print(f"❌ Error uploading {file_name}: {response.status_code} - {response.text}")
                return False
        
        # For large files (>=4MB), use resumable upload session
        else:
            print(f"   Using resumable upload (file size: {file_size / (1024*1024):.2f} MB)...")
            
            # Step 1: Create upload session
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            session_response = requests.post(
                f"https://graph.microsoft.com/v1.0/me/drive/root:/{clean_path}/{file_name}:/createUploadSession",
                headers=headers,
                json={"item": {"@microsoft.graph.conflictBehavior": "replace"}}
            )
            
            if session_response.status_code not in [200, 201]:
                print(f"❌ Error creating upload session: {session_response.status_code} - {session_response.text}")
                return False
            
            upload_url = session_response.json()["uploadUrl"]
            
            # Step 2: Upload file in chunks (10MB chunks)
            chunk_size = 10 * 1024 * 1024  # 10MB chunks
            
            with open(local_file_path, 'rb') as f:
                chunk_number = 0
                while True:
                    chunk = f.read(chunk_size)
                    if not chunk:
                        break
                    
                    start = chunk_number * chunk_size
                    end = start + len(chunk) - 1
                    
                    chunk_headers = {
                        "Content-Length": str(len(chunk)),
                        "Content-Range": f"bytes {start}-{end}/{file_size}"
                    }
                    
                    chunk_response = requests.put(
                        upload_url,
                        headers=chunk_headers,
                        data=chunk
                    )
                    
                    if chunk_response.status_code not in [200, 201, 202]:
                        print(f"❌ Error uploading chunk {chunk_number}: {chunk_response.status_code}")
                        return False
                    
                    chunk_number += 1
                    progress = min(100, (end + 1) * 100 / file_size)
                    print(f"   Progress: {progress:.1f}%", end='\r')
            
            print(f"\n✅ Uploaded: {file_name}")
            return True

# COMMAND ----------

# DBTITLE 1,Internal test using static method
if not skip_tests:
    # Define paths
    model_name = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"
    local_model_dir = "/tmp/RAG/saved_model"
    onedrive_model_path = "/AI/RAG/models/TinyLlama"

    # Create local directory
    os.makedirs(local_model_dir, exist_ok=True)

    print(f"📦 Downloading and saving model: {model_name}")
    print("This may take a few minutes...\n")

    try:
        # Load tokenizer and model
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        model = AutoModelForCausalLM.from_pretrained(
            model_name,
            device_map="cpu",
            torch_dtype="auto"
        )
        
        # Save to local directory
        print(f"💾 Saving model to {local_model_dir}...")
        tokenizer.save_pretrained(local_model_dir)
        model.save_pretrained(local_model_dir)
        print(f"✅ Model saved locally\n")
        
        # Upload to OneDrive
        print(f"☁️ Uploading model files to OneDrive: {onedrive_model_path}\n")
        
        uploaded_count = 0
        failed_count = 0
        
        for file_name in os.listdir(local_model_dir):
            file_path = os.path.join(local_model_dir, file_name)
            if os.path.isfile(file_path):
                file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
                print(f"Uploading {file_name} ({file_size_mb:.2f} MB)...")
                
                if LLMManager.upload_to_onedrive(token, file_path, onedrive_model_path, file_name):
                    uploaded_count += 1
                else:
                    failed_count += 1
        
        print(f"\n📊 Upload Summary:")
        print(f"  ✅ Successful: {uploaded_count} files")
        print(f"  ❌ Failed: {failed_count} files")
        print(f"\n🎉 Model persisted to OneDrive: {onedrive_model_path}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("\n💡 Tip: If you see an authentication error, run Cell 6 again to refresh the token.")

# COMMAND ----------

# from transformers import AutoModelForCausalLM, AutoTokenizer
# import os
# import requests

# def download_folder_from_onedrive(access_token, onedrive_folder_path, local_dir):
#     """
#     Download all files from a OneDrive folder to local directory
#     """
#     headers = {
#         "Authorization": f"Bearer {access_token}",
#         "Content-Type": "application/json"
#     }
    
#     # Clean path
#     clean_path = onedrive_folder_path.strip('/')
    
#     # Get folder contents
#     response = requests.get(
#         f"https://graph.microsoft.com/v1.0/me/drive/root:/{clean_path}:/children",
#         headers=headers
#     )
    
#     if response.status_code != 200:
#         raise Exception(f"Error accessing folder: {response.status_code} - {response.text}")
    
#     items = response.json().get("value", [])
#     os.makedirs(local_dir, exist_ok=True)
    
#     downloaded_count = 0
#     for item in items:
#         if 'file' in item:  # Only download files, not subfolders
#             file_name = item['name']
#             file_id = item['id']
#             local_file_path = os.path.join(local_dir, file_name)
            
#             # Download file content
#             file_response = requests.get(
#                 f"https://graph.microsoft.com/v1.0/me/drive/items/{file_id}/content",
#                 headers={"Authorization": f"Bearer {access_token}"}
#             )
            
#             if file_response.status_code == 200:
#                 with open(local_file_path, 'wb') as f:
#                     f.write(file_response.content)
#                 file_size_mb = len(file_response.content) / (1024 * 1024)
#                 print(f"✅ Downloaded: {file_name} ({file_size_mb:.2f} MB)")
#                 downloaded_count += 1
#             else:
#                 print(f"❌ Error downloading {file_name}: {file_response.status_code}")
    
#     return downloaded_count

# # Define paths
# onedrive_model_path = "/AI/RAG/models/TinyLlama"
# local_model_dir = "/tmp/RAG/loaded_model"

# try:
#     print(f"📥 Downloading model from OneDrive: {onedrive_model_path}\n")
    
#     # Download all model files from OneDrive
#     downloaded = download_folder_from_onedrive(token, onedrive_model_path, local_model_dir)
    
#     print(f"\n✅ Downloaded {downloaded} model files\n")
    
#     # Load the model and tokenizer from the local directory
#     print(f"🤖 Loading model from local directory: {local_model_dir}")
    
#     tokenizer = AutoTokenizer.from_pretrained(local_model_dir)
#     model = AutoModelForCausalLM.from_pretrained(
#         local_model_dir,
#         device_map="cpu",
#         torch_dtype="auto"
#     )
    
#     print("\n🎉 Model loaded successfully from OneDrive!")
#     print(f"Model type: {type(model).__name__}")
#     print(f"Tokenizer vocab size: {len(tokenizer)}")
    
#     # Now you can use this model with LlamaIndex
#     print("\n💡 To use with LlamaIndex (with YOUR exact parameters):")
#     print("\n   from llama_index.core import Settings")
#     print("   from llama_index.llms.huggingface import HuggingFaceLLM")
#     print("\n   Settings.llm = HuggingFaceLLM(")
#     print("       context_window=2048,")
#     print("       max_new_tokens=128,")
#     print("       generate_kwargs={'temperature': 0.3, 'do_sample': True},")
#     print(f"       tokenizer_name='{local_model_dir}',")
#     print(f"       model_name='{local_model_dir}',")
#     print("       device_map='cpu'")
#     print("   )")
#     print("\n📌 Note: The loading code above already uses device_map='cpu'.")
#     print("   Your temperature/do_sample go in generate_kwargs (used during generation).")
#     print("   Only tokenizer_name and model_name change from HF Hub ID to local path!")
    
# except Exception as e:
#     print(f"❌ Error: {e}")
#     print("\n💡 Tip: If you see an authentication error, run Cell 6 again to refresh the token.")

# COMMAND ----------

# DBTITLE 1,LLMManager download method
import os
import requests

class LLMManager:
    """Manager class for LLM operations"""
    
    @staticmethod
    def download_folder_from_onedrive(access_token, onedrive_folder_path, local_dir):
        """
        Download all files from a OneDrive folder to local directory
        """
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        # Clean path
        clean_path = onedrive_folder_path.strip('/')
        
        # Get folder contents
        response = requests.get(
            f"https://graph.microsoft.com/v1.0/me/drive/root:/{clean_path}:/children",
            headers=headers
        )
        
        if response.status_code != 200:
            raise Exception(f"Error accessing folder: {response.status_code} - {response.text}")
        
        items = response.json().get("value", [])
        os.makedirs(local_dir, exist_ok=True)
        
        downloaded_count = 0
        for item in items:
            if 'file' in item:  # Only download files, not subfolders
                file_name = item['name']
                file_id = item['id']
                local_file_path = os.path.join(local_dir, file_name)
                
                # Download file content
                file_response = requests.get(
                    f"https://graph.microsoft.com/v1.0/me/drive/items/{file_id}/content",
                    headers={"Authorization": f"Bearer {access_token}"}
                )
                
                if file_response.status_code == 200:
                    with open(local_file_path, 'wb') as f:
                        f.write(file_response.content)
                    file_size_mb = len(file_response.content) / (1024 * 1024)
                    print(f"✅ Downloaded: {file_name} ({file_size_mb:.2f} MB)")
                    downloaded_count += 1
                else:
                    print(f"❌ Error downloading {file_name}: {file_response.status_code}")
        
        return downloaded_count

# COMMAND ----------

# DBTITLE 1,Internal test for download using static method
if not skip_tests:
    from transformers import AutoModelForCausalLM, AutoTokenizer
    
    # Define paths
    onedrive_model_path = "/AI/RAG/models/TinyLlama"
    local_model_dir = "/tmp/RAG/loaded_model"

    try:
        print(f"📥 Downloading model from OneDrive: {onedrive_model_path}\n")
        
        # Download all model files from OneDrive using static method
        downloaded = LLMManager.download_folder_from_onedrive(token, onedrive_model_path, local_model_dir)
        
        print(f"\n✅ Downloaded {downloaded} model files\n")
        
        # Load the model and tokenizer from the local directory
        print(f"🤖 Loading model from local directory: {local_model_dir}")
        
        tokenizer = AutoTokenizer.from_pretrained(local_model_dir)
        model = AutoModelForCausalLM.from_pretrained(
            local_model_dir,
            device_map="cpu",
            torch_dtype="auto"
        )
        
        print("\n🎉 Model loaded successfully from OneDrive!")
        print(f"Model type: {type(model).__name__}")
        print(f"Tokenizer vocab size: {len(tokenizer)}")
        
        # Usage instructions
        print("\n💡 To use with LlamaIndex:")
        print("\n   from llama_index.core import Settings")
        print("   from llama_index.llms.huggingface import HuggingFaceLLM")
        print("\n   Settings.llm = HuggingFaceLLM(")
        print("       context_window=2048,")
        print("       max_new_tokens=128,")
        print("       generate_kwargs={'temperature': 0.3, 'do_sample': True},")
        print(f"       tokenizer_name='{local_model_dir}',")
        print(f"       model_name='{local_model_dir}',")
        print("       device_map='cpu'")
        print("   )")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("\n💡 Tip: If you see an authentication error, run Cell 6 again to refresh the token.")