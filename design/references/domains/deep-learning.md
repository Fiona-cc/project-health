# 深度学习工程设计包（Deep Learning Domain Pack）

> v1。通用 DL/ML 工程框架——数据、模型、训练、评估、推理、可复现；**不分子方向**。个别方向（RL/检测）的特殊点附在最后，各一小段。

---

## 一、顶层结构

```
project/
  data/             ← 原始数据 + 处理后数据（隔离，各有 readme）
  configs/          ← 实验配置（YAML/JSON，和代码分离）
  models/           ← 模型定义（架构 itself，不含训练循环）
  training/         ← 训练脚本 + 训练循环逻辑
  eval/             ← 评估 / benchmark 脚本
  inference/        ← 推理 / 部署用接口
  utils/            ← 通用工具（metrics、data loading、可视化）
  experiments/      ← 实验记录 + 输出产物（checkpoints、logs、plots）
  notebooks/        ← 探索/可视化 notebook（不是正式代码库的一部分）
```

### 核心原则（和前端一致——职责分离）
- **data vs code vs outputs 三权分立**：数据放 `data/`，代码放 `models/` / `training/`，产物放 `experiments/`。不混在一起。
- **config 和 code 分家**：超参、数据路径、训练轮数 → `configs/experiment_*.yaml`；代码里**不硬编码**配置值。
- **模型定义和训练逻辑分开**：`models/` 只存网络结构（输入→输出）。训练循环、optimizer、scheduler → `training/`。好处：换训练方式不改模型定义；做推理部署直接用模型、不带训练依赖。

---

## 二、数据工程（最容易被忽视的实际工作）

### 原始数据 vs 处理后数据
```
data/
  raw/              ← 原始下载的、外部拿到的——**永不修改**
  processed/        ← 预处理产物（标准化、序列化、特征提取后的）
  external/         ← 预训练权重、词表、外部知识库
```
- `raw/` 是"输入证据"——不可逆地被修改了就丢了可追溯性。**规则：raw 只读。**
- 处理后数据从 raw 运算而来——脚本可重跑、可复现。**规则：处理脚本要在仓库里（cleaning/build_feature.py），处理后产物的格式说清楚。**
- **数据路径别写死在代码里**：从 config 或环境变量取，方便换机器、换集群，避免"只有你原电脑跑得通"。

### 数据规模的基本判断
- 小数据（< 1 GB）→ 直接放仓库或浅层存储，可以版本控制。
- 中数据（1–10 GB）→ 放专用存储（对象存储/网络挂载），代码里存读取方式而非路径。
- 大数据（> 10 GB 或流式）→ 数据管道 streaming，不依赖"全量先下载"。**raw 目录只放元数据和采样样本**。

---

## 三、模型代码 · 训练 · 评估

### 模型定义
- `models/` 每个文件 = 一个模型/backbone，只暴露接口：输入 shape → 输出 shape。**不 import 训练/评估，不 import 数据加载**。
- 和训练分离的好处：想换 backbone？只改 models/。想把训好的模型直接用于推理/部署？直接引用 models/，不拉训练依赖。

### 训练
- 训练入口脚本在 `training/`。训练循环里**只做正常的训练流程**（前向→loss→backward→step 或等效机制）。评估逻辑别挂在训练脚本里——挂在训练里会每轮都对测试集评估，造成**数据泄漏**（test set 参与决策 = 泄漏），评估应该独立跑。
- checkpoint：保存位置放 `experiments/` 下，不放进源码目录。**checkpoint 不进 git**（太大且可重生成）。
- 实验记录：推荐工具（TensorBoard、W&B、MLflow），不自己造轮子写日志。

### 评估
- 评估脚本和训练分开：训练完，用训出来的模型在 eval/ 里独立跑——保证"评估和训练不要用同一次运行"（容易在加载和数据上引入隐性污染）。
- 评估的环境应该**接近最终推理环境**：同样的 batch size、同样的数据加载方式——否则出报告的数字和生产实际不一致。
- 评估前先跑一次完整性检查：数据是否存在、模型文件是否完整、依赖是否满足。

---

## 四、推理 / 部署接口

### 模型的对外接口
- `inference/` 放轻量的"加载模型 → 跑推理 → 返回结果"接口。**不 import training/ 里的循环或数据加载**。
- 接口要成独立模块：将来要换训练方式？不改部署代码。推理环境要瘦，只装真正需要的依赖，不拉整个项目库。

### 接口做好版本管理
- 给接口打 version：`v1` / `v2` → 调用方明确知道用哪个版本、什么时候升级。旧版本同步往前维护几个版本，不能突然挂掉。

---

## 五、可复现性资产（实际工程中最容易塌方的地方）

### 随机种子
- 所有涉及随机的地方——权重初始化、数据 shuffle、dropout——**统一从 config 取种子值**。**单写死在代码里的种子 = 换机器跑不出来一样结果**。
- 种子信息放在实验配置里，和 checkpoint 一起存档；事后别人能拿着同一份 config + 同一份 data 重新跑通。

### 产物隔离
- **每次实验的产物（checkpoints、logs、plots、tensorboard）进单独目录**——不能上一次实验的 checkpoint 盖掉这次的结果。
- **不在源码目录里混放产物**——产物放 `experiments/` 下，源码目录只留代码。

### 环境可复现
- 固定 Python 版本 + 关键依赖（torch / tf / …）的版本号 → `requirements.txt` 或 `environment.yml`。
- 如果有非常规的 C++ 扩展、Docker 环境 → **给清楚 Dockerfile 或安装步骤**，不能假设"这台机器上能跑=别的机器上也能跑"。

---

## 六、典型反模式

| 反模式 | 为什么是问题 | 怎么改 |
|---|---|---|
| 原始数据和预处理产物混放 | 分不清"原始证据"和"派生数据" | raw/ 只读，processed/ 从 raw 脚本生成 |
| 配置硬编码在代码里 | 换实验要改代码，难复现 | 提取到 configs/，参数化 |
| 训练里挂着评估 | 测试集数据泄漏、报告不可靠 | eval/ 独立，跟训练分开跑 |
| checkpoint 进源码 | 仓库大、不可重生成、版本乱 | 放 experiments/ 下，gitignore |
| 没有固定的种子/环境记录 | 换机器跑不出同样结果 | config 里记种子 + 依赖版本 |
| 模型和训练强耦合 | 换训练逻辑要改模型代码 | models/ 独立，不 import training |
| 没有推理接口 | 部署时拉一堆训练依赖 | inference/ 独立模块、只做推理 |

---

## 七、方向专属注解

### 强化学习（RL）
- 核心区别：数据来自环境交互，不是预先收集好的。**环境交互模块独立**（`env/` 或 `envs/`），定义标准接口（`reset / step / get_state / reward`）。
- 探索策略（ε-greedy / noise / entropy）是一个**全局关注点**——放单独模块、多算法复用。
- 经验回放缓冲区（Replay Buffer/Experience Pool）：数据流向不是单次加载，而是持续的采集→存储→采样→更新循环。缓冲区是训练的一部分，和训练逻辑一起管，但和模型本身分离。**训练、探索、回放——三者分开但有明确调用关系**。

### 目标检测
- 标注格式（COCO、Pascal VOC、标注工具的输出）是一个工程关注点——需要格式转换脚本（放 `data/processing/`），不要到处写临时转换代码。
- 数据增强对检测的效果极大——放在数据加载 pipeline 中（`utils/transforms/`），不散落在模型代码里。每个增强项要能单独开关（方便调试）。
- 评估指标（mAP、Precision/Recall、IoU）有现成库（`pycocotools` 等）——直接引用，不自己重写。

---

## 八、权威引用

只指路、不复制：
- PyTorch / TensorFlow / JAX 官方文档
- Hugging Face `transformers` / `datasets` 库结构与约定
- MLflow / W&B / TensorBoard 实验追踪文档
- `cookiecutter-data-science` 目录约定
- COCO / Pascal VOC 标注规范及评估标准
- 各方向社区常用 benchmark 和评估工具

---

## 九、领域包视角（设计顾问怎么拿它说事）

对着一个 DL 项目依次检查：
1. data/ 有 raw/ 和 processed/ 的明确分界吗？raw 是否只读？
2. config 还是在代码里写死的吗？
3. models/ 有训练依赖吗？能直接拿去推理吗？
4. 训练脚本里挂着评估吗？eval/ 是不是独立跑的？
5. 实验产物（checkpoint、log）在 `experiments/` 还是散落各处？
6. 种子/环境/依赖版本固定了吗？别人能复现吗？
7. 有推理接口吗？部署需要拉整个训练依赖吗？
