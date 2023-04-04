from torchvision import models, transforms
import torch

from PIL import Image

# empty spot for resnet model
resnet = None

# define image transform pipeline
preprocess = transforms.Compose([
    transforms.Resize(256),
    transforms.CenterCrop(224),
    transforms.ToTensor(),
    transforms.Normalize(
        mean=[0.485, 0.456, 0.406],
        std=[0.229, 0.224, 0.225]
    )
])

labels = []
with open('imagenet_classes.txt') as f:
    labels = [line.strip() for line in f.readlines()]


def run_resnet(file):
    global resnet
    if resnet is None:
        # load resnet on demand
        resnet = models.resnet152(weights=models.ResNet152_Weights.DEFAULT)
        # eval mode for inference
        resnet.eval()
    # make sure to convert to jpg!!!
    img = Image.open(file).convert('RGB')
    img_t = preprocess(img)
    batch_t = torch.unsqueeze(img_t, 0)

    # run resnet
    out = resnet(batch_t)

    # softmax confidence of all labels
    percentage = torch.nn.functional.softmax(out, dim=1)[0] * 100

    # sort labels by highest confidence
    _, indices = torch.sort(out, descending=True)

    # return top 5 labels in [(label, confidence), ...] format
    return [(labels[idx], percentage[idx].item()) for idx in indices[0][:5]]
