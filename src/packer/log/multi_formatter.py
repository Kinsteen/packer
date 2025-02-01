import logging
import typing as t

from click import style

default_formats = {
    logging.DEBUG: style("DEBUG", fg="cyan") + " | " + style("%(message)s", fg="cyan"),
    logging.INFO: "%(message)s",
    logging.WARNING: style("WARN ", fg="yellow") + " | " + style("%(message)s", fg="yellow"),
    logging.ERROR: style("ERROR", fg="red") + " | " + style("%(message)s", fg="red"),
    logging.CRITICAL: style("FATAL", fg="white", bg="red", bold=True) + " | " + style("%(message)s", fg="red", bold=True),
}


class MultiFormatter(logging.Formatter):
    """Format log messages differently for each log level"""

    def __init__(self, formats: t.Dict[int, str] = None, **kwargs):
        base_format = kwargs.pop("fmt", None)
        super().__init__(base_format, **kwargs)

        formats = formats or default_formats

        self.formatters = {level: logging.Formatter(fmt, **kwargs) for level, fmt in formats.items()}

    def format(self, record: logging.LogRecord):
        formatter = self.formatters.get(record.levelno)

        if formatter is None:
            return super().format(record)

        return formatter.format(record)
