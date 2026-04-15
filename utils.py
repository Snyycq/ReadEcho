"""
ReadEcho Pro 工具函数模块
包含各种工具函数和辅助功能
"""


def format_summary_content(content):
    """
    格式化总结内容，使其更有条理

    Args:
        content: 原始文本内容

    Returns:
        格式化后的HTML内容
    """
    # 如果内容已经是HTML格式，直接返回
    if "<" in content and ">" in content:
        return content

    # 简单的格式化规则：
    # 1. 将"1."、"2."等数字列表转换为有序列表
    # 2. 将"- "、"* "等转换为无序列表
    # 3. 将段落分隔开
    lines = content.split('\n')
    formatted_lines = []
    in_list = False
    list_type = None  # "ol" 或 "ul"

    for line in lines:
        line = line.strip()
        if not line:
            if in_list:
                formatted_lines.append("</li></ul>" if list_type == "ul" else "</li></ol>")
                in_list = False
                list_type = None
            formatted_lines.append("<p></p>")
            continue

        # 检查是否是有序列表项
        if line[:2] in ["1.", "2.", "3.", "4.", "5.", "6.", "7.", "8.", "9."] or line[:3] in ["10.", "11.", "12.", "13.", "14.", "15."]:
            if not in_list or list_type != "ol":
                if in_list:
                    formatted_lines.append("</li></ul>" if list_type == "ul" else "</li></ol>")
                formatted_lines.append("<ol>")
                in_list = True
                list_type = "ol"
            item_text = line[line.find('.') + 1:].strip()
            formatted_lines.append(f"<li>{item_text}</li>")
        # 检查是否是无序列表项
        elif line[:2] in ["- ", "* ", "• "]:
            if not in_list or list_type != "ul":
                if in_list:
                    formatted_lines.append("</li></ul>" if list_type == "ul" else "</li></ol>")
                formatted_lines.append("<ul>")
                in_list = True
                list_type = "ul"
            item_text = line[2:].strip()
            formatted_lines.append(f"<li>{item_text}</li>")
        else:
            if in_list:
                formatted_lines.append("</li></ul>" if list_type == "ul" else "</li></ol>")
                in_list = False
                list_type = None
            # 普通段落
            formatted_lines.append(f"<p>{line}</p>")

    # 关闭最后一个列表
    if in_list:
        formatted_lines.append("</li></ul>" if list_type == "ul" else "</li></ol>")

    return ''.join(formatted_lines)


def truncate_text(text, max_length=50, suffix="..."):
    """
    截断文本，如果超过最大长度则添加后缀

    Args:
        text: 原始文本
        max_length: 最大长度
        suffix: 后缀字符串

    Returns:
        截断后的文本
    """
    if len(text) <= max_length:
        return text
    return text[:max_length] + suffix


def format_timestamp(timestamp):
    """
    格式化时间戳为可读格式

    Args:
        timestamp: 数据库时间戳字符串

    Returns:
        格式化后的时间字符串
    """
    # 简化处理，直接返回原始时间戳
    # 可以扩展为更友好的格式，如"1小时前"、"昨天"等
    return timestamp


def get_theme_button_text(is_dark_mode):
    """
    获取主题按钮文本（图标）

    Args:
        is_dark_mode: 是否为深色模式

    Returns:
        按钮文本（☀️ 或 🌙）
    """
    return "☀️" if is_dark_mode else "🌙"


def format_recording_display_text(text, timestamp):
    """
    格式化录音显示文本

    Args:
        text: 录音文本
        timestamp: 时间戳

    Returns:
        格式化后的显示文本
    """
    display_text = truncate_text(text, 50)
    return f"{timestamp}: {display_text}"