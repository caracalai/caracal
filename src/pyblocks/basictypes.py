class Image:
    def __init__(self, data, height, width):
        self.width = width
        self.height = height
        self.data = data


class Camera:
    def __init__(self, url):
        self.url = url

