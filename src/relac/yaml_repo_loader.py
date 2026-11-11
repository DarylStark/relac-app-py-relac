"""Module with a YAML Repo loader."""

import re
from pathlib import Path
from typing import override

from ruamel.yaml import YAML
from ruamel.yaml.error import MarkedYAMLError

from relac.exceptions import YamlLoadingError

from .repo_loader import RepoLoader


class YamlRepoLoader(RepoLoader):
    """A loader for repo's with YAML files."""

    def __init__(self, repo_path: Path) -> None:
        """Set the initial values."""
        self._path = repo_path

    def discover_files(self) -> list[Path]:
        """Find all YAML files in the working directory."""
        return [
            path
            for pattern in ('*.yaml', '*.yml')
            for path in self._path.rglob(pattern, case_sensitive=True)
            if path.is_file() and not path.name.startswith('_')
        ]

    def _get_include_contents(self, filename: str) -> str:
        """Get the contents for a file that is included."""
        if not filename.startswith('_'):
            raise ValueError('Includes should always start with a underscore.')

        file = Path(self._path / filename)

        if not file.is_file():
            raise ValueError(f'File "{str(file)}" not found.')

        return file.read_text()

    def _preprocess_includes(self, contents: str) -> str:
        """Preprocess include statements.

        User can "include" other YAML files into one by using the directive

           include: "_other_yaml_file.yml"

        The included file has to start with a underscore!.
        """
        return re.sub(
            r'^include: "(?P<filename>.+)"$',
            lambda match: self._get_include_contents(match.group('filename')),
            contents,
            flags=re.MULTILINE,
        )

    def _preprocess_file(self, file: Path) -> str:
        """Preprocess a file."""
        contents = file.read_text()
        contents = self._preprocess_includes(contents)
        return contents

    def _parse_file(self, file: Path, *, parser: YAML) -> list[dict]:
        """Parse a specific file."""
        try:
            contents = self._preprocess_file(file)
        except ValueError as exc:
            raise YamlLoadingError(str(file), exc.args[0]) from exc

        try:
            return list(parser.load_all(contents))
        except MarkedYAMLError as exc:
            raise YamlLoadingError(
                filename=str(file), error=exc.problem
            ) from exc

    def _check_duplicate_keys(self, data: dict[str, list[dict]]) -> None:
        """Check if there are duplicate keys."""
        seen_in: dict[str, str] = {}
        for filename, documents in data.items():
            for document in documents:
                if not isinstance(document, dict):
                    continue

                for key in document:
                    if key.startswith('_'):
                        continue
                    first_file = seen_in.get(key)
                    if first_file is not None:
                        raise YamlLoadingError(
                            filename,
                            f'Key "{key}" is duplicate in file '
                            f'{first_file} and {filename}.',
                        )
                    seen_in[key] = filename

    def _combine_data(self, data: dict[str, list[dict]]) -> dict[str, dict]:
        """Combine the retrieved data into one data dictionary."""
        objects: dict[str, dict] = {}
        for documents in data.values():
            for document in documents:
                if not isinstance(document, dict):
                    continue

                objects.update(
                    (key, value)
                    for key, value in document.items()
                    if not key.startswith('_')
                )

        return objects

    @override
    def retrieve_objects(self) -> dict[str, dict]:
        """Retrieve all objects from the repo."""
        files = self.discover_files()

        yaml_parser = YAML(typ='safe')

        data: dict[str, list[dict]] = {}

        # Load all data
        for file in files:
            data[str(file.relative_to(self._path))] = self._parse_file(
                file, parser=yaml_parser
            )

        self._check_duplicate_keys(data)

        return self._combine_data(data)
