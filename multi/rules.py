import logging
from typing import List, Optional

from multi.errors import RuleParseError

logger = logging.getLogger(__name__)


class Rule:
    def __init__(
        self,
        description: Optional[str] = None,
        globs: Optional[List[str]] = None,
        alwaysApply: bool = False,
        body: str = "",
    ):
        self.description = description
        self.globs = globs
        self.alwaysApply = alwaysApply
        self.body = body

    @staticmethod
    def parse(content: str) -> "Rule":
        """Parse a rule file content into a Rule object."""
        parts = content.split("---\n", 2)
        if len(parts) != 3:
            # Ensure we rstrip to handle cases where the body might be empty or just newlines
            # and split might behave unexpectedly.
            # However, the problem statement implies a fixed structure.
            # For now, stick to the user's existing check.
            raise RuleParseError(
                f"Rule file content does not have frontmatter and body separated by ---: {content[:100]}..."
            )

        frontmatter_str = parts[1]
        body = parts[2]

        description: Optional[str] = None
        globs: Optional[List[str]] = None
        always_apply: bool = False  # Default

        for line in frontmatter_str.splitlines():
            if not line.strip():
                continue  # Skip empty lines

            key_value = line.split(":", 1)
            if len(key_value) != 2:
                # This could be a malformed line, or a line that's not a key-value pair.
                # Depending on strictness, we might raise an error or ignore.
                # For now, let's be somewhat lenient and ignore if not a clear key:value
                # However, the examples suggest a strict key: value format.
                # Re-evaluating: the examples are `key: value` or `key: `
                # So, a missing colon IS an error.
                raise RuleParseError(f"Malformed frontmatter line: {line}")

            key = key_value[0].strip()
            value_str = key_value[1].strip()

            if key == "description":
                description = value_str if value_str else None
            elif key == "globs":
                if value_str:
                    globs = [g.strip() for g in value_str.split(",")]
                else:
                    globs = None
            elif key == "alwaysApply":
                always_apply = value_str.lower() == "true"
            # else:
            # Unknown key, could log a warning or raise error depending on strictness
            # logger.warning(f"Unknown frontmatter key: {key}")

        return Rule(
            description=description,
            globs=globs,
            alwaysApply=always_apply,
            body=body,
        )

    def render(self) -> str:
        """Render rule object back to string format."""
        frontmatter_parts = []

        # Description
        if self.description is not None:
            frontmatter_parts.append(f"description: {self.description}")
        else:
            frontmatter_parts.append("description: ")  # Ensure space for empty value

        # Globs
        if self.globs:
            frontmatter_parts.append(f"globs: {','.join(self.globs)}")
        else:
            frontmatter_parts.append("globs: ")  # Ensure space for empty value

        # alwaysApply
        frontmatter_parts.append(f"alwaysApply: {str(self.alwaysApply).lower()}")

        frontmatter_str = "\n".join(frontmatter_parts) + "\n"  # Add trailing newline

        return f"---\n{frontmatter_str}---\n{self.body}"
