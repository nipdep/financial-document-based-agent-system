
class FileSystemHandler:
    def __init__(self, file_system, **kwargs):
        self.file_system = file_system 

    def add_document(self, request):
        """
        Implemeneted in the Child classes
        """
        pass
    
    def initialize(self):
        """
        Implemeneted in the Child classes
        """
        pass
    
    def get_document(self, request):
        """
        Implemeneted in the Child classes
        """
        pass
    
    def delete_document(self, request):
        """
        Implemeneted in the Child classes
        """
        pass
    