from pathlib import Path
import torch
import torch.nn.functional as F
import torch.optim as optim
from torch.utils.data import DataLoader
from torchvision import datasets, transforms

from se_resnet import se_resnet20
from baseline import resnet20
from utils import Trainer, StepLR


def get_dataloader(batch_size, root="~/.torch/data/cifar10"):
    root = Path(root).expanduser()
    if not root.exists():
        root.mkdir()
    root = str(root)

    to_normalized_tensor = [transforms.ToTensor(),
                            transforms.Normalize((0.4914, 0.4822, 0.4465), (0.2023, 0.1994, 0.2010))]
    data_augmentation = [transforms.RandomCrop(32, padding=4),
                         transforms.RandomHorizontalFlip()]

    train_loader = DataLoader(
            datasets.CIFAR10(root, train=True, download=False,
                             transform=transforms.Compose(data_augmentation + to_normalized_tensor)),
            batch_size=batch_size, shuffle=True)
    test_loader = DataLoader(
            datasets.CIFAR10(root, train=False, transform=transforms.Compose(to_normalized_tensor)),
            batch_size=batch_size, shuffle=True)
    return train_loader, test_loader


def main(batch_size, baseline, reduction, data_path, checkpoint_path, lr, checkpoint_name=None):
    train_loader, test_loader = get_dataloader(batch_size,data_path)

    if baseline:
        model = resnet20()
    else:
        model = se_resnet20(num_classes=10, reduction=reduction)
    optimizer = optim.SGD(params=model.parameters(), lr=lr, momentum=0.9,
                          weight_decay=1e-4)
    scheduler = StepLR(optimizer, 80, 0.1)
    dict = model.state_dict()
    print(dict.keys())
    trainer = Trainer(model, optimizer, F.cross_entropy, save_dir=checkpoint_path)
    # 加载模型参数
    if checkpoint_name!=None:
        checkpoint_path = Path(checkpoint_path)
        ckpt_dir = checkpoint_path / checkpoint_name
        model.load_state_dict(torch.load(ckpt_dir)["weight"])
        print("checkpoint load successfully!")
    trainer.max_acc = max(trainer.test(test_loader),trainer.max_acc)
    trainer.loop(200, train_loader, test_loader, scheduler)

if __name__ == '__main__':
    import argparse

    p = argparse.ArgumentParser()
    p.add_argument("--batchsize", type=int, default=64)
    p.add_argument("--reduction", type=int, default=8)
    p.add_argument("--baseline", action="store_true")
    p.add_argument("--data_path", type=str, default="./data")
    p.add_argument("--checkpoint_path", type=str, default="./checkpoint")
    p.add_argument("--lr", type=float, default=0.1)
    p.add_argument("--checkpoint_name", type=str, default=None)
    args = p.parse_args()
    main(args.batchsize, args.baseline, args.reduction, args.data_path, args.checkpoint_path, args.lr, args.checkpoint_name)
