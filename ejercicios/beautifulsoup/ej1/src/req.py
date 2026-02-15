from urllib.request import urlopen, Request

class Requester():
    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (compatible; Konqueror/3.5.8; Linux)"
        }
        
    def get(self, url):
        return urlopen(Request(url, self.headers))