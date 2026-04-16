# -*- coding: utf-8 -*-
"""Human Thinking Tool Feishu Message Parser Module

飞书消息解析器，用于处理飞书特有的消息格式，包括：
- 回复链消息处理
- @提及处理
- 富文本内容提取
- 引用消息处理
"""

import json
import re
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field


@dataclass
class FeishuMessageInfo:
    """飞书消息信息"""
    message_id: Optional[str] = None
    content: str = ""
    content_type: str = "text"
    reply_to_id: Optional[str] = None
    root_id: Optional[str] = None
    mentions: List[str] = field(default_factory=list)
    is_quote: bool = False
    quote_original: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_memory_metadata(self) -> Dict[str, Any]:
        """转换为记忆元数据"""
        return {
            "message_id": self.message_id,
            "content_type": self.content_type,
            "reply_to_id": self.reply_to_id,
            "root_id": self.root_id,
            "mentions": self.mentions,
            "is_quote": self.is_quote,
            "feishu_metadata": self.metadata
        }


def parse_feishu_content(content: Optional[str]) -> Optional[str]:
    """解析飞书消息内容，提取纯文本

    Args:
        content: 飞书消息内容（JSON格式）

    Returns:
        纯文本内容
    """
    if not content:
        return None

    try:
        data = json.loads(content)
    except json.JSONDecodeError:
        # 如果不是JSON，当作纯文本处理
        return content

    if not isinstance(data, dict):
        return None

    parts = []

    # 提取标题
    title = data.get("title")
    if title and isinstance(title, str) and title.strip():
        parts.append(title.strip())

    # 提取文本内容
    content_blocks = data.get("content") or []
    if isinstance(content_blocks, list):
        for block in content_blocks:
            if not isinstance(block, list):
                continue
            for item in block:
                if not isinstance(item, dict):
                    continue

                tag = item.get("tag")

                # text, code_block, md tags
                if tag in {"text", "code_block", "md"}:
                    text = item.get("text")
                    if isinstance(text, str) and text.strip():
                        parts.append(text.strip())

                # a tag: 链接
                elif tag == "a":
                    text = item.get("text", "")
                    href = item.get("href", "")
                    if href:
                        parts.append(f"[{text}]({href})" if text else href)
                    elif text:
                        parts.append(text.strip())

                # at tag: @提及
                elif tag == "at":
                    user_name = item.get("user_name") or item.get("user_id")
                    if isinstance(user_name, str) and user_name.strip():
                        parts.append(f"@{user_name.strip()}")

    return " ".join(parts) if parts else None


def parse_feishu_reply_chain(content: Optional[str]) -> Dict[str, Any]:
    """解析飞书回复链消息

    Args:
        content: 飞书消息内容

    Returns:
        包含回复链信息的字典
    """
    result = {
        "has_reply": False,
        "reply_to_id": None,
        "root_id": None,
        "quote_content": None
    }

    if not content:
        return result

    try:
        data = json.loads(content)
    except json.JSONDecodeError:
        return result

    if not isinstance(data, dict):
        return result

    # 检查是否是回复消息
    reply_to = data.get("reply_to_message_id") or data.get("quote_message_id")
    if reply_to:
        result["has_reply"] = True
        result["reply_to_id"] = reply_to

    # 检查根消息ID
    root_id = data.get("root_id") or data.get("parent_id")
    if root_id:
        result["root_id"] = root_id

    # 提取引用内容
    quote_content = data.get("quote_content") or data.get("quote") or data.get("original_text")
    if quote_content:
        result["quote_content"] = quote_content if isinstance(quote_content, str) else str(quote_content)

    return result


def extract_mentions(content: Optional[str]) -> List[str]:
    """提取@提及的用户

    Args:
        content: 飞书消息内容

    Returns:
        被提及的用户列表
    """
    mentions = []

    if not content:
        return mentions

    try:
        data = json.loads(content)
    except json.JSONDecodeError:
        return mentions

    if not isinstance(data, dict):
        return mentions

    # 提取content中的at标签
    content_blocks = data.get("content") or []
    if isinstance(content_blocks, list):
        for block in content_blocks:
            if not isinstance(block, list):
                continue
            for item in block:
                if not isinstance(item, dict):
                    continue

                if item.get("tag") == "at":
                    user_name = item.get("user_name") or item.get("user_id")
                    if isinstance(user_name, str) and user_name.strip():
                        mentions.append(user_name.strip())

    return mentions


def parse_feishu_message(content: Optional[str], message_id: Optional[str] = None) -> FeishuMessageInfo:
    """解析完整的飞书消息

    Args:
        content: 飞书消息内容
        message_id: 消息ID

    Returns:
        FeishuMessageInfo对象
    """
    info = FeishuMessageInfo(message_id=message_id)

    if not content:
        return info

    # 解析回复链
    reply_chain = parse_feishu_reply_chain(content)
    info.reply_to_id = reply_chain.get("reply_to_id")
    info.root_id = reply_chain.get("root_id")
    info.is_quote = reply_chain.get("has_reply", False)
    info.quote_original = reply_chain.get("quote_content")

    # 提取纯文本内容
    info.content = parse_feishu_content(content) or ""

    # 提取@提及
    info.mentions = extract_mentions(content)

    # 解析元数据
    try:
        data = json.loads(content)
        if isinstance(data, dict):
            info.metadata = {
                "raw_content": data,
                "title": data.get("title"),
                "msg_type": data.get("msg_type", "post")
            }
    except json.JSONDecodeError:
        pass

    return info


def is_important_feishu_message(content: Optional[str]) -> bool:
    """判断飞书消息是否重要

    重要消息的特征：
    - 有@提及
    - 是回复消息
    - 有引用内容
    - 标题不为空（说明是帖子类型）

    Args:
        content: 飞书消息内容

    Returns:
        是否重要
    """
    if not content:
        return False

    # 有@提及
    mentions = extract_mentions(content)
    if mentions:
        return True

    # 是回复消息
    reply_chain = parse_feishu_reply_chain(content)
    if reply_chain.get("has_reply"):
        return True

    # 有引用内容
    if reply_chain.get("quote_content"):
        return True

    # 有标题（帖子类型）
    try:
        data = json.loads(content)
        if isinstance(data, dict) and data.get("title"):
            return True
    except json.JSONDecodeError:
        pass

    return False
