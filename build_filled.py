import time
import os
import argparse

from processors.cleaner import Cleaner
from processors.theme_packer import ThemePacker
from processors.usage_counter import UsageCounter
from processors.mapping_processor import MappingProcessor
from processors.fill_icon_processor import FillIconProcessor
from processors.fill_shortcut_processor import FillShortcutProcessor

from configs.config import (
    ApiConfig,
    IconConfig,
    CleanConfig,
    FillIconConfig,
    PerformanceConfig,
    ArtifactPathConfig,
    LawniconsPathConfig,
)


def parse_args():
    """解析命令行参数

    支持的参数:
        -fg: 前景色, 例如 "#003a71"
        -bg: 背景色, 例如 "#a1cafe"
        -fill: 填充色, 可选, 留空自动计算
        -test: 是否使用测试目录, 默认False
        -cache: 是否启用填充区域预计算缓存, 加速构建。默认True

    Example:
        启用缓存, 指定填充颜色，使用生产目录:
            python build_filled.py -fg "#003a71" -bg "#a1cafe" -fill "#003a71"
        启用缓存, 不指定填充颜色, 使用生产目录:
            python build_filled.py -fg "#003a71" -bg "#a1cafe"
        禁用缓存, 不指定填充颜色, 使用测试目录:
            python build_filled.py -fg "#003a71" -bg "#a1cafe" -cache false -test
        启用缓存, 不指定填充颜色, 使用测试目录:
            python build_filled.py -fg "#003a71" -bg "#a1cafe" -test

    """
    parser = argparse.ArgumentParser(description="构建Fill风格图标")
    parser.add_argument("-fg", type=str, help="前景色 (例如: #000000)")
    parser.add_argument("-bg", type=str, help="背景色 (例如: #ffffff)")
    parser.add_argument("-fill", type=str, help="填充色, 可选, 留空自动计算")
    parser.add_argument("-test", action="store_true", help="使用测试目录")
    parser.add_argument(
        "-cache", type=str, default="true", help="是否启用填充区域预计算缓存 (true/false)"
    )
    return parser.parse_args()


def build_filled(test_env: bool):
    """构建Fill风格图标主题

    用于构建Fill风格的图标主题
        1. 清理临时文件
        2. 处理图标映射
        3. 处理锁屏快捷方式
        4. 处理应用图标
        5. 打包图标资源
        6. 打包Magisk模块
        7. 清理临时文件

    Args:
        test_env: 是否使用测试环境
            True: 使用test/目录下的测试文件
            False: 使用lawnicons-develop/的完整文件

    工件输出:
        - ./magisk_HyperMonetIcon_filled_{theme_name}_{timestamp}.zip
    """
    print("test_env: ", test_env)

    # 运行前统计
    UsageCounter.request_hits(ApiConfig.api_url_used, ApiConfig.api_headers)

    # 开始时间
    start_time = time.time()

    # 清理临时文件
    print("(1/6) Cleaner: 运行前清理")
    Cleaner.cleanup(CleanConfig.clean_up)

    # 处理映射
    print("\n(2/6) MappingProcessor: 处理映射")
    MappingProcessor.convert_icon_mapper(
        str(LawniconsPathConfig.get_appfilter(test_env)),
        str(ArtifactPathConfig.icon_mapper),
        str(ArtifactPathConfig.icon_mapper_alt),
    )

    # 处理锁屏快捷方式
    print("\n(3/6) FillShortcutProcessor: 处理锁屏快捷方式")
    FillShortcutProcessor.process_lock_shortcut(
        str(LawniconsPathConfig.get_svg_dir(test_env)),
        str(ArtifactPathConfig.icons_template_dir),
        IconConfig.fg_color,
        IconConfig.bg_color,
        FillIconConfig(IconConfig.bg_color).fill_color,
        IconConfig.shortcut_icon_size,
        IconConfig.shortcut_icon_scale,
        PerformanceConfig.supersampling_scale,
    )

    # 处理图标
    print("\n(4/6) FillIconProcessor: 处理图标")
    FillIconProcessor.generate_icons(
        str(ArtifactPathConfig.icon_mapper),
        str(LawniconsPathConfig.get_svg_dir(test_env)),
        str(ArtifactPathConfig.output_dir),
        FillIconConfig(IconConfig.bg_color).fill_color,
        IconConfig.fg_color,
        IconConfig.bg_color,
        IconConfig.icon_size,
        IconConfig.icon_scale,
        PerformanceConfig.supersampling_scale,
        PerformanceConfig.max_workers,
        PerformanceConfig.batch_size_cv,
        PerformanceConfig.batch_size_normal,
        PerformanceConfig.array_pool_size,
        PerformanceConfig.fill_workers,
        PerformanceConfig.background_cache_size,
        PerformanceConfig.enable_fill_mask_cache,
    )

    # 打包icons资源
    print("\n(5/6) ThemePacker: 打包")
    ThemePacker.pack_icons_zip(
        str(ArtifactPathConfig.output_dir),
        str(ArtifactPathConfig.icons_template_dir),
        str(ArtifactPathConfig.mtz_template_dir),
        str(ArtifactPathConfig.magisk_template_dir),
    )

    # 打包magisk模块
    ThemePacker.pack_magisk_module(
        str(ArtifactPathConfig.magisk_template_dir),
        ArtifactPathConfig.target_magisk_pattern_filled,
        ArtifactPathConfig.timestamp,
        ArtifactPathConfig.theme_suffix,
    )

    打包mtz
    ThemePacker.pack_mtz(
        str(ArtifactPathConfig.mtz_template_dir),
        ArtifactPathConfig.target_mtz_pattern,
        ArtifactPathConfig.timestamp,
        ArtifactPathConfig.theme_suffix,
    )

    # 运行后清理
    print("\n(6/6) Cleaner: 运行后清理")
    Cleaner.cleanup(CleanConfig.clean_up)

    print("\n处理完成, 工件已保存至当前目录")
    print("刷入后请重启设备")

    # 总耗时
    total_time = time.time() - start_time
    minutes = int(total_time // 60)
    seconds = total_time % 60
    print(f"\n运行总耗时: {minutes}分{seconds:.1f}秒")

    # 运行后统计
    UsageCounter.request_hits(ApiConfig.api_url_succeed, ApiConfig.api_headers)


if __name__ == "__main__":
    args = parse_args()
    if args.fg:
        IconConfig.fg_color = args.fg
    elif os.getenv("FG_COLOR"):
        IconConfig.fg_color = os.getenv("FG_COLOR")

    if args.bg:
        IconConfig.bg_color = args.bg
    elif os.getenv("BG_COLOR"):
        IconConfig.bg_color = os.getenv("BG_COLOR")

    if args.fill:
        os.environ["FILL_COLOR"] = args.fill

    # 是否使用缓存
    PerformanceConfig.enable_fill_mask_cache = (
        args.cache.lower() == "true"
        if args.cache
        else os.getenv("ENABLE_CACHE", "true").lower() == "true"
    )

    # 是否使用测试目录
    test_env = args.test or os.getenv("TEST_ENV", "False").lower() == "true"
    build_filled(test_env=test_env)
