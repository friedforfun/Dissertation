# from server import evaluate
from models import FlexStudent, resnet32x4
import torch

def convert_onnx(model):
    """

    Convets PyTorch model to ONNX format and saves to ONNX directory.
    Input: PyTorch model object.
    """
    dummy_input = torch.randn(1, 3, 32, 32)

    torch.onnx.export(model, dummy_input, "ONNX/model.onnx", verbose=True)

    print("Model converted to ONNx")


if __name__ == "__main__":


    feasability_genome = [5,5,512,512,512,512,512,1000,1000,1000,1000]

    dummy_input = torch.randn(64, 3, 32, 32)
    # net = FlexStudent([2,3,64,64,64,64,64,64,64,64,64])
    net = resnet32x4(num_classes=100)

    feats, logit = net(dummy_input, is_feat=True, preact=True)

    # some, out = net(dummy_input)
    print(len(feats))
    
    #convert_onnx(net)
