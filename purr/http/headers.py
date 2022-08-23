from __future__ import annotations

from typing import Any, Generator, MutableMapping, Optional


class Headers:
    """A case-insensitive multidict for storing HTTP headers.

    Stores headers in a key-value format. Allows for multiple values
    for a single key.

    Args:
        values: A mapping or list of tuples containing some
        headers to construct from.
    """

    def __init__(self, values: MutableMapping[str, str] | list[tuple[str, str]]):
        self._list: list[tuple[str, str]] = []

        if values:
            if isinstance(values, list):
                self._list = values
            else:
                self._list = list(values.items())

    def __getitem__(self, key: str) -> str:
        """Return the first value for the key.

        Args:
            key (str): The key to look up.

        Returns:
            str: The first value found for the key.

        Raises:
            KeyError: The given key was not found.
        """

        for k, v in self._list:
            if k.lower() == key.lower():
                return v

        raise KeyError(key)

    def __setitem__(self, key: str, value: str):
        """Add a header key/value pair to the multidict

        Args:
            key (str): The key for the value.
            value (str): The value to set.
        """
        self._list.append((key, value))

    def keys(self) -> Generator[str, None, None]:
        """Yield all of the keys in the multidict.

        Yields:
            Generator[str, None, None]: a key from the multidict.
        """
        for key, _ in self._list:
            yield key

    def values(self) -> Generator[str, None, None]:
        """Yield all of the values in the multidict.

        Yields:
            Generator[str, None, None]: A value from the multidict
        """

        for _, value in self._list:
            yield value

    def items(self) -> Generator[tuple[str, str], None, None]:
        """Yield all of the items in the multidict.

        Yields:
            Generator[tuple[str, str], None, None]: A tuple containing a key/value pair.
        """
        yield from self

    def get(self, key: str, default: Optional[Any] = None) -> str | None:
        """Lookup a key, and in the event it doesn't exist, return the default.

        Args:
            key (str): The key to look up.
            default (Optional[str], optional): The default value to return. Defaults to None.

        Returns:
            str: The value corresponding to the key or the default.
        """
        try:
            return self[key]
        except KeyError:
            return default

    def getlist(self, key: str) -> list[str]:
        """Return a list of values for a given key

        Args:
            key (str): The key to look up.

        Returns:
            list[str]: A list consisting of the values for the
            looked up key. Empty if key doesn't exist.
        """

        values: list[str] = []

        for k, v in self._list:
            if k.lower() == key.lower():
                values.append(v)

        return values

    def __contains__(self, key: str) -> bool:
        return any(k.lower() == key.lower() for k, _ in self._list)

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, Headers):
            return False

        return self._list == other._list

    def __len__(self) -> int:
        return len(self._list)

    def __iter__(self) -> Generator[tuple[str, str], None, None]:
        for key, value in self:
            yield key, value
