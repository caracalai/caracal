import numpy as np


class Ndarray:
    def __init__(self, image: np.ndarray):
        self.image = image
        self.shape = image.shape
        self.data_type = str(image.dtype)
