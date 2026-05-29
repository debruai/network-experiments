"""
中文字体配置
确保matplotlib正确显示中文字符
"""

import matplotlib
import matplotlib.pyplot as plt
import os
import sys


def configure_chinese_fonts():
    """
    配置中文字体
    
    尝试使用系统中可用的中文字体，如果找不到则使用默认字体
    """
    # 检查系统平台
    if sys.platform.startswith('linux'):
        # Linux系统：尝试使用Noto Sans CJK字体
        chinese_fonts = [
            'Noto Sans CJK SC',  # 简体中文
            'Noto Sans CJK TC',  # 繁体中文
            'Noto Sans CJK JP',  # 日文
            'Noto Sans CJK KR',  # 韩文
            'DejaVu Sans',
            'Arial Unicode MS',
            'Microsoft YaHei',
            'SimHei',
            'sans-serif'
        ]
    elif sys.platform == 'darwin':
        # macOS系统
        chinese_fonts = [
            'PingFang SC',
            'Hiragino Sans GB',
            'STHeiti',
            'Apple LiGothic',
            'Apple LiSung',
            'Arial Unicode MS',
            'sans-serif'
        ]
    elif sys.platform == 'win32':
        # Windows系统
        chinese_fonts = [
            'Microsoft YaHei',
            'SimHei',
            'SimSun',
            'NSimSun',
            'FangSong',
            'KaiTi',
            'Arial Unicode MS',
            'sans-serif'
        ]
    else:
        # 其他系统
        chinese_fonts = ['sans-serif']
    
    # 过滤出系统中实际可用的字体
    available_fonts = []
    for font in chinese_fonts:
        try:
            # 检查字体是否可用
            font_path = matplotlib.font_manager.findfont(font)
            if font_path and os.path.exists(font_path):
                available_fonts.append(font)
                print(f"找到中文字体: {font} ({font_path})")
        except:
            continue
    
    if available_fonts:
        # 设置字体
        plt.rcParams['font.sans-serif'] = available_fonts
        plt.rcParams['axes.unicode_minus'] = False
        print(f"已设置中文字体: {available_fonts[0]}")
        return True
    else:
        print("警告: 未找到中文字体，将使用默认字体")
        return False


def test_chinese_fonts():
    """测试中文字体是否正常工作"""
    import matplotlib.pyplot as plt
    import numpy as np
    
    # 配置字体
    success = configure_chinese_fonts()
    
    # 创建测试图表
    fig, ax = plt.subplots(figsize=(10, 6))
    
    x = np.linspace(0, 10, 100)
    y = np.sin(x)
    
    ax.plot(x, y, label='正弦曲线')
    ax.set_title('中文字体测试图表', fontsize=16, fontweight='bold')
    ax.set_xlabel('时间 (秒)', fontsize=12)
    ax.set_ylabel('数值', fontsize=12)
    ax.legend(fontsize=10)
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    # 保存测试图表
    test_dir = "font_test"
    os.makedirs(test_dir, exist_ok=True)
    test_path = os.path.join(test_dir, "chinese_font_test.png")
    plt.savefig(test_path, dpi=150, bbox_inches='tight')
    
    print(f"测试图表已保存到: {test_path}")
    
    if success:
        print("✓ 中文字体配置成功")
    else:
        print("✗ 中文字体配置失败，将显示警告")
    
    plt.close(fig)
    return success


if __name__ == "__main__":
    print("=== 中文字体配置测试 ===\n")
    test_chinese_fonts()
