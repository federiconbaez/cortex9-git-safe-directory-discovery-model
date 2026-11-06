"""A tiny in-memory POSIX-like filesystem: absolute paths, owners, devices."""
from __future__ import annotations

import posixpath
from dataclasses import dataclass, field


@dataclass
class Node:
    kind: str  # "dir" or "file"
    owner: int
    device: int = 1
    content: str = ""


@dataclass
class MemFS:
    nodes: dict[str, Node] = field(default_factory=dict)

    @staticmethod
    def norm(path: str) -> str:
        if not path.startswith("/"):
            raise ValueError(f"absolute path required: {path!r}")
        p = posixpath.normpath(path)
        return "/" if p in ("/", "//") else p

    def add(self, path: str, kind: str, owner: int, device: int | None = None, content: str = "") -> None:
        path = self.norm(path)
        parent = posixpath.dirname(path)
        if path != "/" and parent not in self.nodes:
            self.add(parent, "dir", owner, device)
        if device is None:
            device = self.nodes[parent].device if path != "/" and parent in self.nodes else 1
        self.nodes[path] = Node(kind, owner, device, content)

    def get(self, path: str) -> Node | None:
        return self.nodes.get(self.norm(path))

    def is_dir(self, path: str) -> bool:
        n = self.get(path)
        return n is not None and n.kind == "dir"

    def is_file(self, path: str) -> bool:
        n = self.get(path)
        return n is not None and n.kind == "file"

    @classmethod
    def from_spec(cls, spec: list[dict]) -> "MemFS":
        fs = cls()
        fs.add("/", "dir", 0, 1)
        for e in spec:
            fs.add(e["path"], e.get("kind", "dir"), e["owner"], e.get("device"), e.get("content", ""))
        return fs


def join(a: str, b: str) -> str:
    return MemFS.norm(posixpath.join(a, b))


def is_git_directory(fs: MemFS, path: str) -> bool:
    """Simplified ``is_git_directory``: HEAD file plus objects/ and refs/ dirs.

    Real git also validates HEAD's content and honours GIT_OBJECT_DIRECTORY;
    those details are not modelled.
    """
    return fs.is_dir(path) and fs.is_file(join(path, "HEAD")) and fs.is_dir(join(path, "objects")) and fs.is_dir(join(path, "refs"))


def read_gitfile(fs: MemFS, path: str) -> str | None:
    """A ``.git`` *file* of the form ``gitdir: <abs path>`` pointing at a git directory."""
    n = fs.get(path)
    if n is None or n.kind != "file":
        return None
    line = n.content.strip()
    if not line.startswith("gitdir: "):
        return None
    target = line[len("gitdir: "):]
    return target if target.startswith("/") and is_git_directory(fs, target) else None
