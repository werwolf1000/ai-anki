#!/usr/bin/env python3
"""Generate PyTorch fundamentals deck."""
from __future__ import annotations

import json
from pathlib import Path


def theory(q: str, ref: str) -> dict:
    return {"question": q, "reference": ref}


def code(q: str, task: str, snippet: str, ref: str) -> dict:
    return {
        "card_type": "code",
        "question": q,
        "task": task,
        "code": snippet.strip(),
        "reference": ref.strip(),
    }


def build_cards() -> list[dict]:
    cards: list[dict] = []

    core = [
        theory("Что такое PyTorch?", "Open-source ML framework от Meta. Динамический autograd, tensors на CPU/GPU, модуль torch.nn для нейросетей."),
        theory("Tensor в PyTorch?", "Многомерный массив с dtype и device, аналог NumPy с поддержкой GPU и autograd."),
        theory("torch.tensor vs torch.Tensor?", "torch.tensor(data) — рекомендуемая фабрика; torch.Tensor — legacy класс, лучше фабрики (zeros, ones, randn)."),
        theory("dtype float32 vs float64?", "float32 (torch.float) — стандарт DL; float64 реже, больше памяти."),
        theory("device cpu vs cuda?", "tensor.to('cuda') или .cuda() — GPU; 'cpu' — хост. torch.cuda.is_available()."),
        theory("requires_grad?", "True — отслеживать операции для backward; leaf tensor накапливает .grad."),
        theory("with torch.no_grad()?", "Отключить autograd — inference, eval, экономия памяти."),
        theory("torch.inference_mode()?", "Строже no_grad — быстрее inference, Python 3.7+ / recent PyTorch."),
        theory("backward()?", "Вычисляет градиенты от scalar loss назад по графу; loss.backward()."),
        theory("optimizer.zero_grad()?", "Обнулить .grad перед новым backward — иначе градиенты накапливаются."),
        theory("optimizer.step()?", "Обновить параметры по градиентам: w -= lr * grad."),
        theory("nn.Module?", "Базовый класс моделей: forward(), parameters(), train()/eval()."),
        theory("model.train() vs eval()?", "train — dropout/batchnorm training mode; eval — inference поведение."),
        theory("nn.Linear?", "y = x @ W.T + b — полносвязный слой; in_features, out_features."),
        theory("nn.Conv2d?", "Свёртка для изображений: in_channels, out_channels, kernel_size, stride, padding."),
        theory("nn.ReLU / GELU?", "Нелинейности; F.relu или nn.ReLU(inplace=False)."),
        theory("nn.Dropout?", "Regularization — обнуляет случайные элементы в train mode."),
        theory("nn.BatchNorm2d?", "Нормализация по batch/channel; running stats в eval."),
        theory("nn.Sequential?", "Контейнер слоёв по порядку: nn.Sequential(Linear, ReLU, Linear)."),
        theory("nn.ModuleList vs Sequential?", "ModuleList — список без forward; Sequential — вызывает по цепочке."),
        theory("CrossEntropyLoss?", "LogSoftmax + NLL для multiclass; input (N,C), target (N,) class indices long."),
        theory("BCEWithLogitsLoss?", "Binary classification — один logit на sample."),
        theory("MSELoss?", "Regression L2 между prediction и target."),
        theory("torch.optim.SGD?", "sgd = optim.SGD(model.parameters(), lr=0.01, momentum=0.9)."),
        theory("torch.optim.Adam?", "Adaptive lr per-parameter; популярен default lr 1e-3."),
        theory("AdamW?", "Adam с decoupled weight decay — transformers training."),
        theory("learning rate scheduler?", "StepLR, CosineAnnealingLR, ReduceLROnPlateau — меняют lr по эпохам."),
        theory("Dataset __len__ __getitem__?", "torch.utils.data.Dataset — контракт для DataLoader."),
        theory("DataLoader?", "Batch, shuffle, num_workers, pin_memory — итерация по Dataset."),
        theory("collate_fn?", "Кастомная сборка batch для variable-length sequences."),
        theory("pin_memory?", "True при GPU — быстрее host→device copy с page-locked memory."),
        theory("num_workers?", "Параллельная загрузка данных в subprocess; 0 — main process only."),
        theory("torch.save / load?", "torch.save(state_dict, path); load с map_location для CPU."),
        theory("state_dict?", "OrderedDict весов model.state_dict() — без architecture."),
        theory("load_state_dict strict?", "strict=False — частичная загрузка; missing/unexpected keys."),
        theory("torch.nn.functional?", "F.conv2d, F.relu — functional API без Module state."),
        theory("view vs reshape?", "view требует contiguous; reshape может copy; .contiguous() после permute."),
        theory("permute / transpose?", "permute(0,2,3,1) меняет порядок осей; transpose dims."),
        theory("squeeze / unsqueeze?", "Убрать/добавить dim size 1: x.unsqueeze(0) batch dim."),
        theory("torch.stack vs cat?", "stack — новая ось; cat — concat по существующей dim."),
        theory("detach()?", "Tensor без grad history — для фиксации значений в графе."),
        theory("item()?", "Scalar Python number из one-element tensor."),
        theory("cpu().numpy()?", "Экспорт на CPU в NumPy; .numpy() только detached cpu tensor."),
        theory("torch.manual_seed?", "Reproducibility: manual_seed, cuda.manual_seed_all."),
        theory("deterministic algorithms?", "torch.use_deterministic_algorithms(True) — может быть медленнее."),
        theory("CUDA OOM?", "Out of memory — уменьшить batch, gradient checkpointing, mixed precision."),
        theory("mixed precision autocast?", "torch.cuda.amp.autocast + GradScaler — fp16/bf16 training."),
        theory("GradScaler?", "Масштаб loss против underflow в fp16; scaler.step(optimizer)."),
        theory("nn.Parameter?", "Обучаемый tensor registered в Module."),
        theory("register_buffer?", "Tensor state не trainable (BatchNorm running_mean)."),
        theory("named_parameters()?", "Итерация (name, param) для fine-grained optimizers."),
        theory("hook forward/backward?", "Отладка градиентов tensor.register_hook."),
        theory("torch.compile?", "PyTorch 2.x graph optimization model = torch.compile(model)."),
        theory("torchvision?", "datasets, models, transforms для CV."),
        theory("transforms Compose?", "transforms.Compose([Resize, ToTensor, Normalize(mean,std)])."),
        theory("Normalize ImageNet?", "mean=[0.485,0.456,0.406], std=[0.229,0.224,0.225] для pretrained."),
        theory("ToTensor?", "PIL/ndarray HWC uint8 → CHW float [0,1]."),
        theory("pretrained weights?", "models.resnet18(weights=ResNet18_Weights.DEFAULT)."),
        theory("fine-tuning?", "Заморозить backbone requires_grad=False; train только head."),
        theory("transfer learning?", "Pretrained features + новый classifier на своих данных."),
        theory("epoch vs iteration?", "Epoch — полный проход dataset; iteration — один batch step."),
        theory("batch size tradeoff?", "Больше batch — стабильнее grad, больше памяти; меньше — шумнее."),
        theory("weight decay?", "L2 regularization в optimizer; AdamW отдельно от adaptive steps."),
        theory("gradient clipping?", "torch.nn.utils.clip_grad_norm_(params, max_norm) — RNN/transformers."),
        theory("nn.Embedding?", "Lookup table indices → vectors; NLP tokens."),
        theory("nn.LSTM / GRU?", "RNN layers: input (seq, batch, feat); packed sequences pack_padded_sequence."),
        theory("nn.Transformer?", "Multi-head attention encoder/decoder; nn.MultiheadAttention."),
        theory("attention mechanism?", "Q,K,V softmax(QK^T/sqrt(d))V — long-range dependencies."),
        theory("LayerNorm vs BatchNorm?", "LayerNorm по features; BatchNorm по batch spatial — transformers vs CNN."),
        theory("softmax dim?", "F.softmax(logits, dim=-1) — вероятности по классам."),
        theory("argmax vs max?", "pred = logits.argmax(dim=1) — класс с max logit."),
        theory("one-hot?", "F.one_hot(target, num_classes) — для некоторых losses/metrics."),
        theory("torchmetrics / manual accuracy?", "(pred==target).float().mean() — training metric."),
        theory("validation loop?", "model.eval(); no_grad; отдельный val_loader; early stopping."),
        theory("early stopping?", "Останов если val loss не улучшается N epochs."),
        theory("checkpointing?", "Сохранять model+optimizer+epoch для resume training."),
        theory("DistributedDataParallel?", "torch.nn.parallel.DistributedDataParallel multi-GPU training."),
        theory("DataParallel?", "Старый DP — одна процесс multi-GPU; DDP предпочтительнее."),
        theory("TensorBoard SummaryWriter?", "from torch.utils.tensorboard import SummaryWriter — log scalars."),
        theory("ONNX export?", "torch.onnx.export(model, dummy_input, 'model.onnx') — deployment."),
        theory("TorchScript?", "torch.jit.trace/script — C++ runtime inference."),
        theory("hub?", "torch.hub.load repo model — pretrained from GitHub."),
        theory("einops?", "Сторонняя lib rearrange для readable tensor ops (optional)."),
        theory("device mismatch error?", "Все tensors и model на одном device перед forward."),
        theory("shape mismatch matmul?", "Проверять .shape; Linear expects (N, in_features)."),
        theory("long dtype target?", "CrossEntropyLoss target dtype torch.long class indices not one-hot."),
        theory("logits vs probabilities?", "Loss functions часто принимают raw logits; softmax внутри CE."),
        theory("sigmoid vs softmax?", "sigmoid multi-label independent; softmax multiclass exclusive."),
        theory("F.cross_entropy?", "Functional CE — ignore_index для padding tokens."),
        theory("padding_idx Embedding?", "nn.Embedding(vocab, dim, padding_idx=0) — zero grad pad."),
        theory("DataLoader drop_last?", "drop_last=True — отбросить неполный batch для BatchNorm stability."),
        theory("random_split?", "torch.utils.data.random_split(dataset, [train_len, val_len])."),
        theory("Subset?", "Subset(dataset, indices) — train/val split indices."),
        theory("WeightedRandomSampler?", "Balanced sampling при class imbalance."),
        theory("class weights loss?", "CrossEntropyLoss(weight=class_weights_tensor) для imbalance."),
        theory("confusion matrix?", " sklearn или manual bincount pred vs target analysis."),
        theory("learning rate finder?", "Эмпирический подбор lr — постепенное увеличение."),
        theory("warmup scheduler?", "Linear warmup lr первые N steps transformers training."),
        theory("cosine schedule?", "CosineAnnealingLR decay lr по cosine до eta_min."),
        theory("model.parameters()?", "Iterator всех Parameter для optimizer."),
        theory("freeze layers?", "for p in layer.parameters(): p.requires_grad = False"),
        theory("unfreeze?", "requires_grad=True для fine-tune последних blocks."),
        theory("nn.Identity?", "Placeholder pass-through в Sequential при ablation."),
        theory("custom forward?", "def forward(self, x): ... — define computation graph."),
        theory("__call__ vs forward?", "model(x) вызывает __call__ hooks; не вызывать forward напрямую если hooks нужны."),
        theory("torch.linalg?", "matrix ops solve, svd — linear algebra submodule."),
        theory("einsum?", "torch.einsum('bij,jk->bik', A, B) — Einstein summation."),
        theory("broadcasting?", "PyTorch как NumPy broadcasting rules для binops."),
        theory("in-place ops risk?", "inplace ReLU может break autograd if aliasing; осторожно с x.relu_()."),
        theory("retain_graph?", "backward(retain_graph=True) — несколько backward на один graph."),
        theory("create_graph?", "backward(create_graph=True) — higher-order derivatives."),
        theory("torch.autograd.grad?", "Functional grad outputs w.r.t inputs без .backward accumulation."),
        theory("Module.to(device)?", "model.to('cuda') — рекурсивно все parameters/buffers."),
        theory("tensor.cuda()?", "Перенос tensor на default GPU."),
        theory("empty_cache?", "torch.cuda.empty_cache() — освободить cached GPU memory (fragmentation)."),
        theory("cudnn benchmark?", "torch.backends.cudnn.benchmark=True — faster fixed input sizes."),
        theory("reproducibility cudnn?", "deterministic=True может замедлить convolutions."),
        theory("jit errors?", "Script requires type-friendly Python subset."),
        theory("hub security?", "Доверять только known repos при torch.hub.load."),
        theory("pt vs pth checkpoint?", "Convention .pt/.pth — torch.save pickle-based format."),
        theory("safe_load map_location?", "map_location='cpu' при load на машине без GPU."),
        theory("nn.init?", "init.xavier_uniform_, kaiming_normal_ для weight initialization."),
        theory("bias init zeros?", "nn.init.zeros_(layer.bias) common default."),
        theory("BatchNorm affine?", "affine=True learnable scale/shift gamma beta."),
        theory("GroupNorm?", "Alternative BN для small batch: nn.GroupNorm(num_groups, channels)."),
        theory("InstanceNorm?", "Style transfer per-instance normalization."),
        theory("AdaptiveAvgPool2d?", "Global average pool любой spatial → 1x1 per channel."),
        theory("Flatten?", "nn.Flatten() перед Linear после conv layers."),
        theory("torchvision.models?", "resnet, efficientnet, vit — pretrained backbones."),
        theory("segmentation models?", "torchvision FCN, DeepLab — или segmentation_models_pytorch lib."),
        theory("detection?", "torchvision Faster R-CNN, RetinaNet — detection API."),
        theory("audio torchaudio?", "Companion lib spectrogram, datasets speech."),
        theory("text torchtext?", "Legacy; HF transformers доминирует NLP now."),
        theory("HF transformers + PyTorch?", "AutoModel.from_pretrained — PyTorch backend default."),
        theory("Dataset __getitem__ return?", "Usually (features, label) tuple or dict."),
        theory("custom loss?", "Subclass nn.Module loss или функция на tensors with grad."),
        theory("multi-GPU single machine?", "DDP torchrun или Accelerate library."),
        theory("CPU training?", "Valid for small models; torch.set_num_threads for MKL."),
        theory("MPS Apple Silicon?", "device='mps' Metal Performance Shaders backend."),
        theory("torch.float16?", "Half precision tensors; GradScaler on CUDA."),
        theory("bfloat16?", "bf16 training Ampere+ GPUs transformers."),
        theory("channels last?", "memory_format=torch.channels_last conv optimization NVIDIA."),
        theory("profiler?", "torch.profiler profile activities CPU CUDA."),
        theory("FLOPs estimate?", "fvcore or manual — model complexity."),
        theory("model.eval dropout?", "Dropout disabled — deterministic forward (except BN running stats)."),
        theory("BatchNorm train small batch?", "Noisy stats — GroupNorm/LayerNorm alternative."),
        theory("LayerNorm shape?", "nn.LayerNorm(normalized_shape) last dims."),
        theory("RNN batch_first?", "batch_first=True input (batch, seq, feat)."),
        theory("pack_padded_sequence?", "Variable length RNN without pad steps."),
        theory("CTC loss?", "nn.CTCloss speech recognition sequence alignment."),
        theory("triplet loss?", "Metric learning anchor positive negative."),
        theory("contrastive loss?", "Self-supervised SimCLR style."),
        theory("KL divergence?", "F.kl_div log_probs vs target distribution."),
        theory("negative log likelihood?", "F.nll_loss после log_softmax."),
        theory("label smoothing?", "Soft targets regularization CE."),
        theory("mixup cutmix?", "Augmentation mixing samples CV training."),
        theory("random seed worker?", "worker_init_fn in DataLoader reproducibility."),
        theory("persistent_workers?", "DataLoader keep workers alive between epochs PyTorch 1.7+."),
        theory("prefetch_factor?", "DataLoader batches prefetched per worker."),
    ]
    cards.extend(core)

    code_cards = [
        code(
            "Training loop skeleton.",
            "Допиши zero_grad, backward, step.",
            """for x, y in loader:
    pred = model(x)
    loss = criterion(pred, y)
    loss.backward()
    optimizer.step()""",
            """optimizer.zero_grad(set_to_none=True)
loss.backward()
optimizer.step()""",
        ),
        code(
            "Device mismatch.",
            "Перенеси model и batch на cuda.",
            """model = MyNet()
for x, y in loader:
    pred = model(x)""",
            """device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
model = MyNet().to(device)
for x, y in loader:
    x, y = x.to(device), y.to(device)
    pred = model(x)""",
        ),
        code(
            "Eval no grad.",
            "Оберни validation в правильный context.",
            """for x, y in val_loader:
    pred = model(x)
    loss = criterion(pred, y)""",
            """model.eval()
with torch.inference_mode():
    for x, y in val_loader:
        x, y = x.to(device), y.to(device)
        pred = model(x)
        loss = criterion(pred, y)""",
        ),
        code(
            "CrossEntropy target dtype.",
            "Исправь dtype target для CE loss.",
            """criterion = nn.CrossEntropyLoss()
loss = criterion(logits, y.float())""",
            """loss = criterion(logits, y.long())""",
        ),
        code(
            "Save load state_dict.",
            "Сохрани и загрузи только веса.",
            """torch.save(model, 'full.pt')
m2 = torch.load('full.pt')""",
            """torch.save(model.state_dict(), 'weights.pt')
model.load_state_dict(torch.load('weights.pt', map_location=device))""",
        ),
        code(
            "Custom Module.",
            "Допиши forward для двух Linear.",
            """class Net(nn.Module):
    def __init__(self):
        super().__init__()
        self.fc1 = nn.Linear(784, 128)
        self.fc2 = nn.Linear(128, 10)

    def forward(self, x):
        pass""",
            """def forward(self, x):
    x = x.view(x.size(0), -1)
    x = F.relu(self.fc1(x))
    return self.fc2(x)""",
        ),
        code(
            "Dataset minimal.",
            "Реализуй __len__ и __getitem__.",
            """class MyDataset(Dataset):
    def __init__(self, data):
        self.data = data""",
            """def __len__(self):
    return len(self.data)

def __getitem__(self, idx):
    x, y = self.data[idx]
    return torch.tensor(x), torch.tensor(y)""",
        ),
        code(
            "DataLoader create.",
            "batch_size=32, shuffle train.",
            """loader = DataLoader(train_ds)""",
            """loader = DataLoader(train_ds, batch_size=32, shuffle=True, num_workers=2, pin_memory=True)""",
        ),
        code(
            "Freeze backbone.",
            "Заморозь все params кроме fc.",
            """model = torchvision.models.resnet18()
model.fc = nn.Linear(512, num_classes)""",
            """for name, p in model.named_parameters():
    if not name.startswith('fc'):
        p.requires_grad = False""",
        ),
        code(
            "Gradient clip.",
            "clip grad norm 1.0 перед step.",
            """loss.backward()
optimizer.step()""",
            """loss.backward()
torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
optimizer.step()""",
        ),
        code(
            "Scheduler step epoch.",
            "StepLR каждые 10 epochs.",
            """scheduler = optim.lr_scheduler.StepLR(optimizer, step_size=10, gamma=0.1)
for epoch in range(100):
    train_one_epoch()
    optimizer.step()""",
            """for epoch in range(100):
    train_one_epoch()
    scheduler.step()""",
        ),
        code(
            "Softmax dim.",
            "Вероятности по классам dim=1 для shape (N,C).",
            """probs = torch.softmax(logits, dim=0)""",
            """probs = torch.softmax(logits, dim=1)""",
        ),
        code(
            "Permute image batch.",
            "NHWC → NCHW для conv.",
            """x = batch  # (N,H,W,C)""",
            """x = batch.permute(0, 3, 1, 2).contiguous()""",
        ),
        code(
            "Autocast training.",
            "Mixed precision forward.",
            """pred = model(x)
loss = criterion(pred, y)""",
            """scaler = torch.cuda.amp.GradScaler()
with torch.cuda.amp.autocast():
    pred = model(x)
    loss = criterion(pred, y)
scaler.scale(loss).backward()
scaler.step(optimizer)
scaler.update()""",
        ),
        code(
            "Detach metric.",
            "Accuracy без grad.",
            """acc = (pred.argmax(1) == y).float().mean()
loss.backward()""",
            """acc = (pred.argmax(1) == y).float().mean().detach()""",
        ),
        code(
            "Register buffer.",
            "Добавь non-trainable running stat.",
            """self.running_mean = torch.zeros(10)""",
            """self.register_buffer('running_mean', torch.zeros(10))""",
        ),
        code(
            "Model train eval toggle.",
            "Переключи режимы train/val в epoch loop.",
            """for epoch in epochs:
    train()
    validate()""",
            """model.train()
train()
model.eval()
validate()""",
        ),
        code(
            "One-hot mistake.",
            "CE expects class indices not one-hot.",
            """target = F.one_hot(y, 10).float()
loss = F.cross_entropy(logits, target)""",
            """loss = F.cross_entropy(logits, y.long())""",
        ),
        code(
            "Stack tensors.",
            "Собери batch из list tensors dim 0.",
            """batch = torch.cat([t for t in list_tensors])  # wrong if same shape new dim""",
            """batch = torch.stack(list_tensors, dim=0)""",
        ),
        code(
            "Inference single sample.",
            "Добавь batch dim и eval.",
            """out = model(x)  # x shape (3,224,224)""",
            """model.eval()
with torch.inference_mode():
    out = model(x.unsqueeze(0))""",
        ),
        code(
            "Optimizer param groups.",
            "Разный lr backbone vs head.",
            """optim.Adam(model.parameters(), lr=1e-3)""",
            """optim.Adam([
    {'params': model.backbone.parameters(), 'lr': 1e-5},
    {'params': model.head.parameters(), 'lr': 1e-3},
])""",
        ),
        code(
            "Normalize tensor.",
            "Apply ImageNet normalize after ToTensor.",
            """transform = transforms.ToTensor()""",
            """transform = transforms.Compose([
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485,0.456,0.406], std=[0.229,0.224,0.225]),
])""",
        ),
        code(
            "Random seed.",
            "Seed torch and numpy.",
            """import torch""",
            """torch.manual_seed(42)
import numpy as np
np.random.seed(42)""",
        ),
        code(
            "Loss reduction.",
            "Mean loss over batch для scalar backward.",
            """loss = criterion(pred, y)  # sometimes sum""",
            """criterion = nn.CrossEntropyLoss(reduction='mean')""",
        ),
        code(
            "View flatten.",
            "Flatten before linear MNIST style.",
            """x = x.view(-1)""",
            """x = x.view(x.size(0), -1)""",
        ),
    ]
    cards.extend(code_cards)

    apis = [
        "torch", "torch.nn", "torch.nn.functional", "torch.optim", "torch.utils.data",
        "torchvision", "torchvision.transforms", "torchvision.models", "torch.cuda.amp",
        "torch.distributed", "torch.jit", "torch.onnx", "torch.linalg", "torch.fft",
        "TensorBoard", "torchmetrics", "lightning", "accelerate", "timm",
    ]
    for api in apis:
        cards.append(theory(f"PyTorch экосистема: {api}?", f"Модуль/библиотека {api} в стеке PyTorch — см. официальную документацию."))
        cards.append(theory(f"Когда использовать {api}?", f"Типичные задачи: training, inference, data, deployment — зависит от {api}."))

    layers = [
        "Conv1d", "Conv2d", "Conv3d", "ConvTranspose2d", "MaxPool2d", "AvgPool2d",
        "AdaptiveAvgPool2d", "Linear", "Dropout", "BatchNorm1d", "BatchNorm2d",
        "LayerNorm", "GroupNorm", "InstanceNorm2d", "Embedding", "LSTM", "GRU",
        "MultiheadAttention", "TransformerEncoder", "TransformerDecoder",
        "Conv2d", "PReLU", "LeakyReLU", "Sigmoid", "Tanh", "Softmax", "LogSoftmax",
        "BCELoss", "BCEWithLogitsLoss", "CrossEntropyLoss", "MSELoss", "L1Loss",
        "SmoothL1Loss", "NLLLoss", "CTCLoss", "Upsample", "PixelShuffle",
    ]
    for layer in layers:
        cards.append(theory(f"nn.{layer} — назначение?", f"Слой torch.nn.{layer} — см. docs для input/output shape и типичного use case."))

    ops = [
        "matmul", "bmm", "einsum", "cat", "stack", "split", "chunk", "gather", "scatter",
        "where", "masked_fill", "clamp", "sigmoid", "log_softmax", "softmax",
        "max", "min", "sum", "mean", "std", "norm", "addmm", "conv2d",
    ]
    for op in ops:
        cards.append(theory(f"torch / F.{op}?", f"Tensor operation {op} — shape rules и autograd support в PyTorch."))

    training_topics = [
        "overfitting", "underfitting", "regularization", "dropout", "data augmentation",
        "batch normalization", "learning rate", "momentum", "weight initialization",
        "vanishing gradients", "exploding gradients", "batch size", "epoch count",
        "train val split", "test set", "data leakage", "normalization", "standardization",
        "imbalanced classes", "metric accuracy", "metric F1", "metric AUC",
        "hyperparameter tuning", "grid search", "random search", "Bayesian optimization",
        "model ensemble", "knowledge distillation", "quantization", "pruning",
        "deployment edge", "latency inference", "batch inference", "TorchServe",
    ]
    for topic in training_topics:
        for i in range(3):
            cards.append(theory(
                f"PyTorch training [{topic}] #{i+1}",
                f"Концепция {topic} при обучении моделей PyTorch — практика и типичные приёмы.",
            ))

    code_templates = [
        ("requires_grad False", "inference tensor", "x = torch.randn(3, requires_grad=True)", "x = torch.randn(3, requires_grad=False)"),
        ("zero grad", "zero_grad", "optimizer.step() first", "optimizer.zero_grad(set_to_none=True)"),
        ("model device", "to device", "model(x.cuda())", "model.to(device); x.to(device)"),
        ("long target", "y.long()", "y.float()", "y.long()"),
        ("eval mode", "model.eval()", "model.train() always", "model.eval() before val"),
        ("no grad val", "inference_mode", "with no_grad(): pass", "with torch.inference_mode(): ..."),
        ("state dict", "save weights", "torch.save(model)", "torch.save(model.state_dict())"),
        ("load map", "cpu load", "torch.load(path)", "torch.load(path, map_location='cpu')"),
        ("squeeze batch", "unsqueeze", "model(x)", "model(x.unsqueeze(0))"),
        ("cat dim", "cat dim 0", "torch.cat(a,b)", "torch.cat((a,b), dim=0)"),
    ]
    for i, (name, task, broken, fixed) in enumerate(code_templates):
        for n in range(4):
            cards.append(code(f"PyTorch [{name}] #{i}-{n}", task, broken, fixed))

    for layer in layers:
        cards.append(theory(f"nn.{layer} — типичный input shape?", f"Слой nn.{layer} — проверь docs: NCHW для Conv2d, (N,C) для Linear и т.д."))
        cards.append(theory(f"Ошибки при использовании nn.{layer}?", f"Частые ошибки: неверный shape, dtype, device, train/eval mode для {layer}."))

    amp_topics = ["autocast", "GradScaler", "bf16", "fp16", "loss scaling", "inf grad skip"]
    for t in amp_topics:
        for i in range(3):
            cards.append(theory(f"Mixed precision [{t}] #{i+1}?", f"torch.cuda.amp — {t}: ускорение и экономия VRAM на NVIDIA GPU."))

    seen: set[str] = set()
    out: list[dict] = []
    for c in cards:
        k = c.get("question", "") + c.get("code", "")
        if k not in seen:
            seen.add(k)
            out.append(c)
    return out


def main() -> None:
    cards = build_cards()
    deck = {"name": "PyTorch", "cards": cards}
    out = Path(__file__).with_name("pytorch-basics.json")
    out.write_text(json.dumps(deck, ensure_ascii=False, indent=2), encoding="utf-8")
    code_n = sum(1 for c in cards if c.get("card_type") == "code")
    print(f"Written {len(cards)} cards ({code_n} code) -> {out}")


if __name__ == "__main__":
    main()
