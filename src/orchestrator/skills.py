"""
Skill Loader - Shared utility for loading agent skills.

Provides centralized skill loading for all Radcod agents.
"""

import logging
from pathlib import Path
from typing import Optional, List

logger = logging.getLogger("radcod.skills")

# Default skills directory - in agents module
DEFAULT_SKILLS_DIR = Path(__file__).parent.parent / "agents" / "skills"


def load_skill(skill_name: str, skills_dir: Path = None) -> Optional[str]:
    """
    Load a skill from markdown file.
    
    Args:
        skill_name: Name of the skill file (without .md)
        skills_dir: Optional custom skills directory
        
    Returns:
        Skill content as string, or None if not found
    """
    skill_path = (skills_dir or DEFAULT_SKILLS_DIR) / f"{skill_name}.md"
    
    if not skill_path.exists():
        logger.warning(f"Skill not found: {skill_path}")
        return None
    
    try:
        with open(skill_path, "r") as f:
            content = f.read()
            
        # Skip YAML frontmatter (---)
        lines = content.split("\n")
        start = 0
        for i, line in enumerate(lines):
            # Skip frontmatter delimiter and metadata
            if line.startswith("---"):
                continue
            if line.startswith("# "):
                start = i
                break
        
        result = "\n".join(lines[start:])
        logger.debug(f"Loaded skill: {skill_name}")
        return result
        
    except Exception as e:
        logger.error(f"Failed to load skill {skill_name}: {e}")
        return None


def list_skills(skills_dir: Path = None) -> list:
    """
    List available skills.
    
    Args:
        skills_dir: Optional custom skills directory
        
    Returns:
        List of skill names (without .md)
    """
    skill_dir = skills_dir or DEFAULT_SKILLS_DIR
    
    if not skill_dir.exists():
        return []
    
    return [f.stem for f in skill_dir.glob("*.md")]


def get_skill_dir(custom_path: str = None) -> Path:
    """
    Get skills directory, with optional override.
    
    Args:
        custom_path: Optional custom path from env/config
        
    Returns:
        Path to skills directory
    """
    if custom_path:
        return Path(custom_path)
    return DEFAULT_SKILLS_DIR