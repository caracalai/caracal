import numpy


class Ndarray:
    def __init__(self, image: numpy.ndarray):
        self.image = image
        self.shape = image.shape


class Camera:
    def __init__(self, url):
        self.url = url
