# 即梦AI Python SDK

即梦AI Python SDK 提供了简洁的 API 接口封装，支持图像生成、视频生成等功能。

## 安装

```bash
pip install -r requirements.txt
```

## 初始化客户端

```python
from jimeng.sdk.jimeng_client import JimengClient

# 使用您的refresh token初始化客户端
client = JimengClient("your_refresh_token_here")
```

## 功能列表

- [文本生成图像](#文本生成图像文生图)
- [图像生成图像](#图像生成图像图生图)
- [文本生成视频](#文本生成视频文生视频)
- [图像生成视频](#图像生成视频图生视频)
- [积分管理](#积分管理)

## 文本生成图像（文生图）

根据文本描述生成图像。

### 基本用法

```python
# 生成图像
images = client.generate_images(
    prompt="一只可爱的猫咪在花园里玩耍",
    model="jimeng-4.0"
)

# images是一个包含图像URL的列表
for image_url in images:
    print(f"生成的图像: {image_url}")
```

### 参数说明

| 参数 | 类型 | 必需 | 默认值 | 说明 |
|------|------|------|--------|------|
| prompt | str | 是 | - | 图像生成提示词 |
| model | str | 否 | "jimeng-4.0" | 模型名称 |
| options | dict | 否 | None | 其他选项参数 |

### options参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| ratio | str | "1:1" | 图像比例 |
| resolution | str | "2k" | 分辨率 |
| sampleStrength | float | 0.5 | 采样强度 |
| negativePrompt | str | "" | 负面提示词 |

### 示例

```python
# 使用自定义参数生成图像
images = client.generate_images(
    prompt="一只可爱的猫咪在花园里玩耍",
    model="jimeng-4.0",
    options={
        "ratio": "16:9",
        "resolution": "2k",
        "sampleStrength": 0.7,
        "negativePrompt": "模糊,低质量"
    }
)
```

## 图像生成图像（图生图）

基于现有图像生成新图像。

### 基本用法

```python
# 读取本地图片文件
with open("image.png", "rb") as f:
    image_data = f.read()

# 图像合成
images = client.generate_image_composition(
    prompt="将这张图片转换为油画风格",
    images=[image_data],  # 可以是多个图像
    model="jimeng-4.0"
)

# images是一个包含图像URL的列表
for image_url in images:
    print(f"合成的图像: {image_url}")
```

### 使用图片URL

```python
# 使用图片URL
images = client.generate_image_composition(
    prompt="将这张图片转换为油画风格",
    images=["https://example.com/image.jpg"],
    model="jimeng-4.0"
)
```

### 参数说明

| 参数 | 类型 | 必需 | 默认值 | 说明 |
|------|------|------|--------|------|
| prompt | str | 是 | - | 图像合成提示词 |
| images | List[Union[str, bytes]] | 是 | - | 输入图像列表 |
| model | str | 否 | "jimeng-4.0" | 模型名称 |
| options | dict | 否 | None | 其他选项参数 |

### options参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| ratio | str | "1:1" | 图像比例 |
| resolution | str | "2k" | 分辨率 |
| sampleStrength | float | 0.5 | 采样强度 |
| negativePrompt | str | "" | 负面提示词 |

### 示例

```python
# 使用自定义参数进行图像合成
with open("image.png", "rb") as f:
    image_data = f.read()

images = client.generate_image_composition(
    prompt="将这张图片转换为油画风格",
    images=[image_data],
    model="jimeng-4.0",
    options={
        "ratio": "3:4",
        "resolution": "2k",
        "sampleStrength": 0.6
    }
)
```

## 文本生成视频（文生视频）

根据文本描述生成视频。

### 基本用法

```python
# 生成视频
video_url = client.generate_video(
    prompt="一只小猫在花园里玩耍的视频",
    model="jimeng-video-3.0"
)

print(f"生成的视频: {video_url}")
```

### 参数说明

| 参数 | 类型 | 必需 | 默认值 | 说明 |
|------|------|------|--------|------|
| prompt | str | 是 | - | 视频生成提示词 |
| model | str | 否 | "jimeng-video-3.0" | 模型名称 |
| options | dict | 否 | None | 其他选项参数 |

### options参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| width | int | 1024 | 视频宽度 |
| height | int | 1024 | 视频高度 |
| resolution | str | "720p" | 分辨率 |

### 示例

```python
# 使用自定义参数生成视频
video_url = client.generate_video(
    prompt="一只小猫在花园里玩耍的视频",
    model="jimeng-video-3.0",
    options={
        "width": 512,
        "height": 512,
        "resolution": "480p"
    }
)

print(f"生成的视频: {video_url}")
```

## 图像生成视频（图生视频）

基于现有图像生成视频。

### 基本用法

```python
# 使用本地图片文件生成视频
video_url = client.generate_video(
    prompt="基于这张图片生成一个动态视频",
    model="jimeng-video-3.0",
    options={
        "filePaths": ["/path/to/image.png"]
    }
)

print(f"生成的视频: {video_url}")
```

### 参数说明

| 参数 | 类型 | 必需 | 默认值 | 说明 |
|------|------|------|--------|------|
| prompt | str | 是 | - | 视频生成提示词 |
| model | str | 否 | "jimeng-video-3.0" | 模型名称 |
| options | dict | 否 | None | 其他选项参数 |

### options参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| width | int | 1024 | 视频宽度 |
| height | int | 1024 | 视频高度 |
| resolution | str | "720p" | 分辨率 |
| duration_ms | int | 5000 | 视频时长，可选值为 5000 或 10000 |
| filePaths | List[str] | - | 图片文件路径列表 |

### 示例

```
# 使用自定义参数生成视频
video_url = client.generate_video(
    prompt="基于这张图片生成一个动态视频",
    model="jimeng-video-3.0",
    options={
        "width": 512,
        "height": 512,
        "resolution": "480p",
        "duration_ms": 5000,
        "filePaths": ["/path/to/image.png"]
    }
)

print(f"生成的视频: {video_url}")
```

## 积分管理

### 获取积分信息

```python
credit_info = client.get_credit()
print(f"总积分: {credit_info['totalCredit']}")
```

### 接收今日积分

```python
receive_result = client.receive_credit()
print(f"今日收取积分: {receive_result['receive_quota']}")
```

## 错误处理

SDK使用自定义异常处理错误：

```python
from jimeng.sdk.lib.exceptions.api_exception import APIException

try:
    images = client.generate_images("一只可爱的猫咪")
except APIException as e:
    print(f"API错误: {e}")
except Exception as e:
    print(f"其他错误: {e}")
```

## 支持的模型

### 图像生成模型

- `nanobanana`: 仅国际站支持
- `jimeng-4.0`: 国内、国际站均支持
- `jimeng-3.1`: 仅国内站支持
- `jimeng-3.0`: 国内、国际站均支持
- `jimeng-2.1`: 仅国内站支持
- `jimeng-xl-pro`: 国内站支持

### 视频生成模型

- `jimeng-video-3.0-pro`: 专业版
- `jimeng-video-3.0`: 标准版
- `jimeng-video-2.0-pro`: 专业版v2
- `jimeng-video-2.0`: 标准版v2

## 分辨率选项

### 图像分辨率

支持的图像分辨率和比例：

| 分辨率 | 比例 | 分辨率尺寸 |
|--------|------|------------|
| 1k | 1:1 | 1328×1328 |
| 1k | 4:3 | 1472×1104 |
| 1k | 3:4 | 1104×1472 |
| 1k | 16:9 | 1664×936 |
| 1k | 9:16 | 936×1664 |
| 1k | 3:2 | 1584×1056 |
| 1k | 2:3 | 1056×1584 |
| 1k | 21:9 | 2016×864 |
| 2k (默认) | 1:1 | 2048×2048 |
| 2k (默认) | 4:3 | 2304×1728 |
| 2k (默认) | 3:4 | 1728×2304 |
| 2k (默认) | 16:9 | 2560×1440 |
| 2k (默认) | 9:16 | 1440×2560 |
| 2k (默认) | 3:2 | 2496×1664 |
| 2k (默认) | 2:3 | 1664×2496 |
| 2k (默认) | 21:9 | 3024×1296 |
| 4k | 1:1 | 4096×4096 |
| 4k | 4:3 | 4608×3456 |
| 4k | 3:4 | 3456×4608 |
| 4k | 16:9 | 5120×2880 |
| 4k | 9:16 | 2880×5120 |
| 4k | 3:2 | 4992×3328 |
| 4k | 2:3 | 3328×4992 |
| 4k | 21:9 | 6048×2592 |

### 视频分辨率

- `720p`
- `1080p`

## 比例选项

### 图像比例

- `1:1`
- `3:4`
- `4:3`
- `16:9`
- `9:16`
- `3:2`
- `2:3`
- `21:9`