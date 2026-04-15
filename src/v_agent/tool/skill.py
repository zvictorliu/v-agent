import os
from pathlib import Path
from typing import Dict, Any, Optional
import yaml
from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field


class SkillManager:
    def __init__(self):
        self.skills: Dict[str, Dict[str, str]] = {}
        self._load_skills()

    def _load_skills(self):
        # 扫描目录
        search_dirs = [
            Path.home() / ".claude" / "skills",
            Path.cwd() / ".claude" / "skills",
            Path.cwd() / ".opencode" / "skills",
        ]

        for d in search_dirs:
            if not d.exists() or not d.is_dir():
                continue

            # 查找所有 SKILL.md 文件
            for skill_file in d.rglob("SKILL.md"):
                self._parse_skill_file(skill_file)

    def _parse_skill_file(self, file_path: Path):
        try:
            content = file_path.read_text(encoding="utf-8")
            # 提取 frontmatter
            if content.startswith("---"):
                end_idx = content.find("---", 3)
                if end_idx != -1:
                    frontmatter_str = content[3:end_idx].strip()
                    body = content[end_idx + 3 :].strip()
                    try:
                        meta = yaml.safe_load(frontmatter_str)
                        if isinstance(meta, dict) and "name" in meta:
                            name = meta["name"]
                            desc = meta.get("description", f"Skill: {name}")

                            self.skills[name] = {
                                "name": name,
                                "description": desc,
                                "path": str(file_path),
                                "content": body,
                                "dir": str(file_path.parent),
                            }
                    except yaml.YAMLError:
                        pass  # Ignore parsing errors
        except Exception:
            pass

    def get_skill_description_prompt(self) -> str:
        if not self.skills:
            return "Load a skill to get detailed instructions for a specific task. No skills are currently available."

        prompt_lines = [
            "Load a skill to get detailed instructions for a specific task.",
            "Skills provide specialized knowledge and step-by-step guidance.",
            "Use this when a task matches an available skill's description.",
            "<available_skills>",
        ]

        for name, info in self.skills.items():
            prompt_lines.append("  <skill>")
            prompt_lines.append(f"    <name>{name}</name>")
            prompt_lines.append(f"    <description>{info['description']}</description>")
            prompt_lines.append("  </skill>")

        prompt_lines.append("</available_skills>")
        return "\n".join(prompt_lines)

    def execute_skill(self, skill_name: str) -> str:
        if skill_name not in self.skills:
            available = ", ".join(self.skills.keys())
            return f"Error: Skill '{skill_name}' not found. Available skills: {available or 'none'}"

        skill = self.skills[skill_name]
        return f"## Skill: {skill['name']}\n\n**Base directory**: {skill['dir']}\n\n{skill['content']}"


# 全局 SkillManager 实例
_skill_manager = SkillManager()


def get_available_skills() -> Dict[str, str]:
    """供外部（例如 CLI）获取当前已加载的 skills 列表的简要信息"""
    return {name: info["description"] for name, info in _skill_manager.skills.items()}


class SkillInput(BaseModel):
    skill_name: str = Field(description="The skill identifier from available_skills.")


def create_skill_tool():
    desc = _skill_manager.get_skill_description_prompt()

    return StructuredTool.from_function(
        func=_skill_manager.execute_skill,
        name="skill",
        description=desc,
        args_schema=SkillInput,
    )


skill_tool = create_skill_tool()
