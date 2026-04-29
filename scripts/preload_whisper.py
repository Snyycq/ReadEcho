"""
预下载Whisper模型到本地缓存
运行一次即可，之后启动应用时模型会从缓存加载，速度很快
"""

import sys
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))


def main():
    cache_dir = Path.home() / ".readecho" / "models"
    cache_dir.mkdir(parents=True, exist_ok=True)
    print(f"缓存目录: {cache_dir}")

    try:
        import torch

        print(f"PyTorch版本: {torch.__version__}")
        print(f"CUDA可用: {torch.cuda.is_available()}")
    except ImportError:
        print("错误: PyTorch未安装，请先运行: pip install torch")
        return

    try:
        import whisper

        print("Whisper已安装")
    except ImportError:
        print("错误: Whisper未安装，请先运行: pip install openai-whisper")
        return

    # 下载tiny模型（最小，约75MB）
    model_size = "tiny"
    print(f"\n正在下载Whisper {model_size}模型...")
    print("首次下载需要几分钟，请耐心等待...")

    try:
        device = "cuda" if torch.cuda.is_available() else "cpu"
        whisper.load_model(model_size, device=device, download_root=str(cache_dir / "whisper"))
        print(f"\n✓ 模型下载完成！已缓存到: {cache_dir}")
        print(f"  模型大小: {model_size}")
        print(f"  设备: {device}")
        print("\n下次启动应用时，模型将从本地缓存加载，速度会很快。")
    except Exception as e:
        print(f"\n✗ 下载失败: {e}")
        print("请检查网络连接后重试。")


if __name__ == "__main__":
    main()
