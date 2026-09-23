"""Load the model registry and predict without training or weather downloads."""
import src
from src.ml_final import predict_final

if __name__ == "__main__":
    predict_final()
