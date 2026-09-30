
class _Logger:
    def __init__(self) -> None:
        self.clear()

    def empty(self) -> bool:
        return len(self._results) == 0

    def write(self, value: str = "") -> None:
        self._results.append(value)

    def writeAll(self, values: list[str]) -> None:
        for value in values:
            self._results.append(value)

    def error(self, value: str = "") -> None:
        self.write(value)
        self.setError()

    def errorAll(self, values: list[str]) -> None:
        self.writeAll(values)
        self.setError()

    def setError(self, ev: bool = True) -> None:
        self._errored = self._errored or ev

    def hasErrored(self) -> bool:
        return self._errored

    def clear(self) -> None:
        self._results = []
        self._errored = False

    def print(self) -> str:
        return self.__str__()

    def flush(self) -> str:
        results = self.print()
        self.clear()

        return results

    def __str__(self) -> str:
        return "\n".join([result for result in self._results])

Logger = _Logger()
