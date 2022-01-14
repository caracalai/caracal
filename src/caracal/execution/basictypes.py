import numpy as np


class Ndarray:
    def __init__(self, data: np.ndarray):
        self.data = data
        self.shape = data.shape
        self.data_type = str(data.dtype)
