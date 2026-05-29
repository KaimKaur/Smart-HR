from __future__ import annotations

import csv
from io import StringIO
from typing import Iterable

from fastapi.responses import StreamingResponse


def generate_csv(
    *,
    headers: list[str],
    rows: Iterable[Iterable],
    filename: str,
) -> StreamingResponse:
    def stream():
        buffer = StringIO()
        writer = csv.writer(buffer)

        writer.writerow(headers)
        yield buffer.getvalue()
        buffer.seek(0)
        buffer.truncate(0)

        for row in rows:
            writer.writerow(row)
            yield buffer.getvalue()
            buffer.seek(0)
            buffer.truncate(0)

    return StreamingResponse(
        stream(),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
