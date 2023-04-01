from torchvision import models, transforms
import torch

from PIL import Image

resnet = models.resnet152(pretrained=True)
resnet.eval()

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
    img = Image.open(file)
    img_t = preprocess(img)
    batch_t = torch.unsqueeze(img_t, 0)

    out = resnet(batch_t)

    percentage = torch.nn.functional.softmax(out, dim=1)[0] * 100

    _, indices = torch.sort(out, descending=True)

    return [(labels[idx], percentage[idx].item()) for idx in indices[0][:5]]
