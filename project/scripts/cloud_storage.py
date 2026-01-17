"""
Cloud storage abstraction for AWS S3 and Azure Blob Storage.
"""

import os
from pathlib import Path
from typing import Optional

class CloudStorage:
    """Abstract interface for cloud storage"""
    
    def __init__(self, provider: str = 'local'):
        """
        Initialize cloud storage client.
        
        Args:
            provider: 'local', 'aws', or 'azure'
        """
        self.provider = provider.lower()
        self.client = None
        
        if self.provider == 'aws':
            self._init_aws()
        elif self.provider == 'azure':
            self._init_azure()
        elif self.provider == 'local':
            pass  # No initialization needed
        else:
            raise ValueError(f"Unknown provider: {provider}")
    
    def _init_aws(self):
        """Initialize AWS S3 client"""
        try:
            import boto3
            self.client = boto3.client('s3')
            self.bucket = os.environ.get('AWS_S3_BUCKET', '')
            if not self.bucket:
                print("Warning: AWS_S3_BUCKET not set")
        except ImportError:
            print("boto3 not installed. Install with: pip install boto3")
            self.client = None
    
    def _init_azure(self):
        """Initialize Azure Blob Storage client"""
        try:
            from azure.storage.blob import BlobServiceClient
            connection_string = os.environ.get('AZURE_STORAGE_CONNECTION_STRING', '')
            if not connection_string:
                print("Warning: AZURE_STORAGE_CONNECTION_STRING not set")
                self.client = None
            else:
                self.client = BlobServiceClient.from_connection_string(connection_string)
                self.container = os.environ.get('AZURE_CONTAINER_NAME', 'research-papers')
        except ImportError:
            print("azure-storage-blob not installed. Install with: pip install azure-storage-blob")
            self.client = None
    
    def upload_file(self, local_path: str, remote_path: str) -> bool:
        """
        Upload file to cloud storage.
        
        Args:
            local_path: Local file path
            remote_path: Remote path/key
            
        Returns:
            True if successful
        """
        if self.provider == 'local':
            # For local, just copy to output directory
            import shutil
            os.makedirs(os.path.dirname(remote_path) or '.', exist_ok=True)
            shutil.copy2(local_path, remote_path)
            return True
        
        elif self.provider == 'aws':
            if not self.client or not self.bucket:
                print("AWS S3 not properly configured")
                return False
            
            try:
                self.client.upload_file(local_path, self.bucket, remote_path)
                print(f"✓ Uploaded to s3://{self.bucket}/{remote_path}")
                return True
            except Exception as e:
                print(f"✗ AWS upload failed: {e}")
                return False
        
        elif self.provider == 'azure':
            if not self.client:
                print("Azure Blob Storage not properly configured")
                return False
            
            try:
                blob_client = self.client.get_blob_client(
                    container=self.container,
                    blob=remote_path
                )
                
                with open(local_path, 'rb') as data:
                    blob_client.upload_blob(data, overwrite=True)
                
                print(f"✓ Uploaded to Azure: {self.container}/{remote_path}")
                return True
            except Exception as e:
                print(f"✗ Azure upload failed: {e}")
                return False
        
        return False
    
    def download_file(self, remote_path: str, local_path: str) -> bool:
        """
        Download file from cloud storage.
        
        Args:
            remote_path: Remote path/key
            local_path: Local file path
            
        Returns:
            True if successful
        """
        if self.provider == 'local':
            # For local, just copy
            import shutil
            os.makedirs(os.path.dirname(local_path) or '.', exist_ok=True)
            shutil.copy2(remote_path, local_path)
            return True
        
        elif self.provider == 'aws':
            if not self.client or not self.bucket:
                return False
            
            try:
                os.makedirs(os.path.dirname(local_path) or '.', exist_ok=True)
                self.client.download_file(self.bucket, remote_path, local_path)
                print(f"✓ Downloaded from s3://{self.bucket}/{remote_path}")
                return True
            except Exception as e:
                print(f"✗ AWS download failed: {e}")
                return False
        
        elif self.provider == 'azure':
            if not self.client:
                return False
            
            try:
                blob_client = self.client.get_blob_client(
                    container=self.container,
                    blob=remote_path
                )
                
                os.makedirs(os.path.dirname(local_path) or '.', exist_ok=True)
                
                with open(local_path, 'wb') as f:
                    f.write(blob_client.download_blob().readall())
                
                print(f"✓ Downloaded from Azure: {self.container}/{remote_path}")
                return True
            except Exception as e:
                print(f"✗ Azure download failed: {e}")
                return False
        
        return False
    
    def list_files(self, prefix: str = '') -> list:
        """
        List files in cloud storage.
        
        Args:
            prefix: Prefix to filter files
            
        Returns:
            List of file paths
        """
        if self.provider == 'local':
            # List local files
            path = Path(prefix) if prefix else Path('.')
            if path.is_dir():
                return [str(p) for p in path.rglob('*') if p.is_file()]
            return []
        
        elif self.provider == 'aws':
            if not self.client or not self.bucket:
                return []
            
            try:
                response = self.client.list_objects_v2(
                    Bucket=self.bucket,
                    Prefix=prefix
                )
                return [obj['Key'] for obj in response.get('Contents', [])]
            except Exception as e:
                print(f"✗ AWS list failed: {e}")
                return []
        
        elif self.provider == 'azure':
            if not self.client:
                return []
            
            try:
                container_client = self.client.get_container_client(self.container)
                blobs = container_client.list_blobs(name_starts_with=prefix)
                return [blob.name for blob in blobs]
            except Exception as e:
                print(f"✗ Azure list failed: {e}")
                return []
        
        return []
    
    def file_exists(self, remote_path: str) -> bool:
        """
        Check if file exists in cloud storage.
        
        Args:
            remote_path: Remote path/key
            
        Returns:
            True if file exists
        """
        if self.provider == 'local':
            return os.path.exists(remote_path)
        
        elif self.provider == 'aws':
            if not self.client or not self.bucket:
                return False
            
            try:
                self.client.head_object(Bucket=self.bucket, Key=remote_path)
                return True
            except:
                return False
        
        elif self.provider == 'azure':
            if not self.client:
                return False
            
            try:
                blob_client = self.client.get_blob_client(
                    container=self.container,
                    blob=remote_path
                )
                return blob_client.exists()
            except:
                return False
        
        return False

def get_storage_client(provider: Optional[str] = None) -> CloudStorage:
    """
    Get cloud storage client based on environment or explicit choice.
    
    Args:
        provider: Explicitly specify 'local', 'aws', or 'azure'
                 If None, auto-detect from environment
    
    Returns:
        CloudStorage instance
    """
    if provider is None:
        # Auto-detect from environment
        if os.environ.get('AWS_S3_BUCKET'):
            provider = 'aws'
        elif os.environ.get('AZURE_STORAGE_CONNECTION_STRING'):
            provider = 'azure'
        else:
            provider = 'local'
    
    return CloudStorage(provider)

if __name__ == '__main__':
    # Test storage client
    storage = get_storage_client('local')
    
    print(f"Using provider: {storage.provider}")
    
    # Test file operations
    test_file = 'test.txt'
    with open(test_file, 'w') as f:
        f.write('Test content')
    
    # Upload
    storage.upload_file(test_file, 'outputs/test.txt')
    
    # Check existence
    exists = storage.file_exists('outputs/test.txt')
    print(f"File exists: {exists}")
    
    # Cleanup
    os.remove(test_file)