from __future__ import annotations

import argparse
import hashlib
import json
import random
from pathlib import Path

import numpy as np
import torch
import yaml
from torch.utils.data import DataLoader, Dataset
from transformers import (
    AutoModelForSequenceClassification,
    AutoTokenizer,
    get_linear_schedule_with_warmup,
)


class JsonlTextDataset(Dataset):
    def __init__(self, path: Path):
        with path.open("r", encoding="utf-8") as handle:
            self.rows = [json.loads(line) for line in handle if line.strip()]

    def __len__(self) -> int:
        return len(self.rows)

    def __getitem__(self, index: int) -> dict:
        return self.rows[index]


def collate_fn(batch, tokenizer, max_length):
    texts = [row["text"] for row in batch]
    labels = torch.tensor([row["label"] for row in batch], dtype=torch.long)
    encoded = tokenizer(
        texts,
        padding=True,
        truncation=True,
        max_length=max_length,
        return_tensors="pt",
    )
    encoded["labels"] = labels
    return encoded


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("ml/configs/security_detector_v0_1.yaml"),
    )
    return parser.parse_args()


def load_config(repo_root: Path, config_path: Path) -> dict:
    path = config_path if config_path.is_absolute() else repo_root / config_path
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def set_seed(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


@torch.no_grad()
def predict(model, loader, device):
    model.eval()
    all_labels = []
    all_probs = []

    for batch in loader:
        batch = {key: value.to(device) for key, value in batch.items()}
        labels = batch.pop("labels")
        outputs = model(**batch)
        probs = torch.softmax(outputs.logits, dim=-1)[:, 1]
        all_labels.extend(labels.cpu().numpy().tolist())
        all_probs.extend(probs.cpu().numpy().tolist())

    return np.asarray(all_labels), np.asarray(all_probs)


def main() -> None:
    args = parse_args()
    repo_root = args.repo_root.resolve()
    config = load_config(repo_root, args.config)

    seed = int(config["experiment"]["seed"])
    set_seed(seed)

    dataset_dir = repo_root / config["paths"]["dataset_artifacts"]
    train_ds = JsonlTextDataset(dataset_dir / "train.jsonl")
    val_ds = JsonlTextDataset(dataset_dir / "validation.jsonl")

    model_name = config["model"]["name"]
    model_revision = config["model"]["revision"]
    max_length = int(config["model"]["max_length"])
    batch_size = int(config["training"]["batch_size"])
    epochs = int(config["training"]["epochs"])
    learning_rate = float(config["training"]["learning_rate"])
    weight_decay = float(config["training"]["weight_decay"])
    warmup_ratio = float(config["training"]["warmup_ratio"])
    clip_norm = float(config["training"]["gradient_clip_norm"])

    tokenizer = AutoTokenizer.from_pretrained(model_name, revision=model_revision)
    model = AutoModelForSequenceClassification.from_pretrained(
        model_name,
        revision=model_revision,
        num_labels=int(config["model"]["num_labels"]),
        id2label={0: "benign", 1: "harmful"},
        label2id={"benign": 0, "harmful": 1},
    )

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model.to(device)

    train_loader = DataLoader(
        train_ds,
        batch_size=batch_size,
        shuffle=True,
        collate_fn=lambda batch: collate_fn(batch, tokenizer, max_length),
    )
    val_loader = DataLoader(
        val_ds,
        batch_size=batch_size,
        shuffle=False,
        collate_fn=lambda batch: collate_fn(batch, tokenizer, max_length),
    )

    optimizer = torch.optim.AdamW(
        model.parameters(),
        lr=learning_rate,
        weight_decay=weight_decay,
    )

    total_steps = len(train_loader) * epochs
    warmup_steps = int(total_steps * warmup_ratio)
    scheduler = get_linear_schedule_with_warmup(
        optimizer,
        num_warmup_steps=warmup_steps,
        num_training_steps=total_steps,
    )

    best_f1 = -1.0
    best_state = None

    from sklearn.metrics import f1_score

    for epoch in range(1, epochs + 1):
        model.train()
        total_loss = 0.0

        for batch in train_loader:
            batch = {key: value.to(device) for key, value in batch.items()}
            optimizer.zero_grad(set_to_none=True)

            outputs = model(**batch)
            loss = outputs.loss
            loss.backward()

            torch.nn.utils.clip_grad_norm_(model.parameters(), clip_norm)

            optimizer.step()
            scheduler.step()

            total_loss += float(loss.detach().cpu())

        labels, probs = predict(model, val_loader, device)
        predictions = (probs >= 0.50).astype(int)
        f1 = float(f1_score(labels, predictions, zero_division=0))

        average_loss = total_loss / max(len(train_loader), 1)
        print(
            f"epoch={epoch} "
            f"train_loss={average_loss:.6f} "
            f"val_f1@0.50={f1:.6f}"
        )

        if f1 > best_f1:
            best_f1 = f1
            best_state = {
                key: value.detach().cpu().clone()
                for key, value in model.state_dict().items()
            }

    if best_state is None:
        raise RuntimeError("No model checkpoint was selected.")

    model.load_state_dict(best_state)

    model_dir = repo_root / config["paths"]["model_artifacts"]
    model_dir.mkdir(parents=True, exist_ok=True)

    model.save_pretrained(model_dir)
    tokenizer.save_pretrained(model_dir)

    dataset_manifest = dataset_dir / "manifest.json"
    metadata = {
        "experiment": config["experiment"],
        "dataset_manifest_sha256": hashlib.sha256(dataset_manifest.read_bytes()).hexdigest(),
        "model_name": model_name,
        "model_revision": model_revision,
        "device": str(device),
        "seed": seed,
        "epochs": epochs,
        "batch_size": batch_size,
        "learning_rate": learning_rate,
        "best_validation_f1_at_0_50": best_f1,
    }

    with (model_dir / "training_metadata.json").open("w", encoding="utf-8") as handle:
        json.dump(metadata, handle, indent=2)

    print(f"Model saved to: {model_dir}")


if __name__ == "__main__":
    main()
