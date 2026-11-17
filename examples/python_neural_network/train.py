"""Первая нейросеть: классификация Iris на CPU, без скачивания датасета."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import torch
from sklearn.datasets import load_iris
from sklearn.dummy import DummyClassifier
from sklearn.metrics import accuracy_score, confusion_matrix
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from torch import nn
from torch.utils.data import DataLoader, TensorDataset


def make_model() -> nn.Module:
    # Четыре измерения цветка → 16 скрытых нейронов → три класса.
    # CrossEntropyLoss ожидает logits, поэтому Softmax здесь не нужен.
    return nn.Sequential(nn.Linear(4, 16), nn.ReLU(), nn.Linear(16, 3))


def train(output: Path, epochs: int = 100, seed: int = 42) -> dict:
    if epochs < 1:
        raise ValueError("Число эпох должно быть положительным")
    torch.manual_seed(seed)
    torch.set_num_threads(1)
    iris = load_iris(as_frame=True)
    features = iris.data.to_numpy(dtype=np.float32)
    labels = iris.target.to_numpy(dtype=np.int64)

    # Test откладываем до конца. Validation используется только для выбора эпохи.
    x_pool, x_test, y_pool, y_test = train_test_split(
        features, labels, test_size=0.2, stratify=labels, random_state=seed,
    )
    x_train, x_val, y_train, y_val = train_test_split(
        x_pool, y_pool, test_size=0.25, stratify=y_pool, random_state=seed,
    )
    scaler = StandardScaler().fit(x_train)

    def tensor(x):
        return torch.tensor(scaler.transform(x), dtype=torch.float32)

    dataset = TensorDataset(tensor(x_train), torch.tensor(y_train, dtype=torch.long))
    batches = DataLoader(dataset, batch_size=16, shuffle=True, num_workers=0,
                         generator=torch.Generator().manual_seed(seed))
    val_x, val_y = tensor(x_val), torch.tensor(y_val, dtype=torch.long)
    model = make_model()
    loss_fn = nn.CrossEntropyLoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=0.01)
    best_loss, best_state, best_epoch = float("inf"), None, 0
    history = []
    for epoch in range(1, epochs + 1):
        model.train()
        total_loss = 0.0
        for x_batch, y_batch in batches:
            optimizer.zero_grad()
            loss = loss_fn(model(x_batch), y_batch)
            loss.backward()
            optimizer.step()
            total_loss += loss.item() * len(y_batch)
        model.eval()
        with torch.inference_mode():
            logits = model(val_x)
            val_loss = loss_fn(logits, val_y).item()
            val_accuracy = (logits.argmax(dim=1) == val_y).float().mean().item()
        history.append({"epoch": epoch, "train_loss": total_loss / len(dataset),
                        "val_loss": val_loss, "val_accuracy": val_accuracy})
        if val_loss < best_loss:
            best_loss, best_epoch = val_loss, epoch
            best_state = {name: value.detach().clone() for name, value in model.state_dict().items()}

    model.load_state_dict(best_state)
    model.eval()
    with torch.inference_mode():
        predicted = model(tensor(x_test)).argmax(dim=1).numpy()
    baseline = DummyClassifier(strategy="most_frequent").fit(x_train, y_train)
    metrics = {
        "seed": seed, "epochs": epochs, "best_epoch": best_epoch,
        "train_size": len(y_train), "validation_size": len(y_val), "test_size": len(y_test),
        "test_accuracy": float(accuracy_score(y_test, predicted)),
        "baseline_accuracy": float(accuracy_score(y_test, baseline.predict(x_test))),
        "confusion_matrix": confusion_matrix(y_test, predicted, labels=[0, 1, 2]).tolist(),
    }
    output.mkdir(parents=True, exist_ok=True)
    # Сохраняем также порядок признаков и параметры нормализации для инференса.
    torch.save({"state_dict": best_state, "mean": scaler.mean_.tolist(), "scale": scaler.scale_.tolist(),
                "features": list(iris.feature_names), "classes": iris.target_names.tolist()}, output / "model.pt")
    (output / "metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    (output / "history.json").write_text(json.dumps(history, indent=2), encoding="utf-8")
    iris.frame.to_csv(output / "iris.csv", index=False)
    return metrics


def predict(checkpoint: Path, values: list[float]) -> dict:
    if len(values) != 4 or not np.isfinite(values).all():
        raise ValueError("Нужны четыре конечных числа: размеры чашелистика и лепестка в сантиметрах")
    data = torch.load(checkpoint, map_location="cpu", weights_only=True)
    model = make_model()
    model.load_state_dict(data["state_dict"])
    model.eval()
    features = (np.asarray(values, dtype=np.float32) - np.asarray(data["mean"])) / np.asarray(data["scale"])
    with torch.inference_mode():
        probabilities = model(torch.tensor(features, dtype=torch.float32).unsqueeze(0)).softmax(dim=1)[0]
    index = int(probabilities.argmax())
    return {"class": data["classes"][index], "probabilities": dict(zip(data["classes"], probabilities.tolist()))}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("data/python-neural-network"))
    parser.add_argument("--epochs", type=int, default=100)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--predict", type=float, nargs=4, metavar=("SEPAL_L", "SEPAL_W", "PETAL_L", "PETAL_W"))
    args = parser.parse_args()
    if args.epochs < 1:
        parser.error("--epochs должен быть положительным")
    result = predict(args.output / "model.pt", args.predict) if args.predict else train(args.output, args.epochs, args.seed)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
