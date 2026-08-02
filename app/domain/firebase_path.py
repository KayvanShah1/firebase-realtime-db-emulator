from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class FirebasePath:
    """A parsed Firebase path with helpers for the v2 MongoDB representation."""

    raw: str
    segments: tuple[str, ...]

    @classmethod
    def parse(cls, path: str) -> "FirebasePath":
        normalized = path.strip("/")
        if not normalized:
            raise ValueError("Firebase path cannot be empty")

        segments = tuple(normalized.split("/"))
        if any(not segment for segment in segments):
            raise ValueError("Firebase path cannot contain empty segments")
        return cls(raw=normalized, segments=segments)

    @property
    def collection(self) -> str:
        return self.segments[0]

    @property
    def record_id(self) -> str | None:
        return self.segments[1] if len(self.segments) > 1 else None

    @property
    def child_segments(self) -> tuple[str, ...]:
        return self.segments[2:]

    @property
    def is_collection(self) -> bool:
        return self.record_id is None

    @property
    def mongo_value_path(self) -> str:
        suffix = ".".join(self.child_segments)
        return f"_fm_val.{suffix}" if suffix else "_fm_val"

    @property
    def mongo_parent_path(self) -> str:
        suffix = ".".join(self.child_segments[:-1])
        return f"_fm_val.{suffix}" if suffix else "_fm_val"

    def append(self, relative_path: str) -> "FirebasePath":
        return self.parse(f"{self.raw}/{relative_path}")
