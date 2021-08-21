import singer
import singer.metrics as metrics
from singer import metadata
from singer.bookmarks import get_bookmark
from tap_sitehq.utility import (
    get_generic,
    formatDate,
)


async def handle_resource(session, resource, schemas, state, mdata):
    extraction_time = singer.utils.now()
    bookmark = get_bookmark(state, resource, "since")
    qs = {"updated_since": bookmark} if bookmark else {}

    with metrics.record_counter(resource) as counter:
        for row in await get_generic(session, resource, resource, qs):
            write_record(row, resource, schemas[resource], mdata, extraction_time)
            counter.increment()

    return (resource, extraction_time)


# More convenient to use but has to all be held in memory, so use write_record instead for resources with many rows
def write_many(rows, resource, schema, mdata, dt):
    with metrics.record_counter(resource) as counter:
        for row in rows:
            write_record(row, resource, schema, mdata, dt)
            counter.increment()


def write_record(row, resource, schema, mdata, dt):
    with singer.Transformer() as transformer:
        rec = transformer.transform(row, schema, metadata=metadata.to_map(mdata))
    singer.write_record(resource, rec, time_extracted=dt)


def write_bookmark(state, resource, dt):
    singer.write_bookmark(state, resource, "since", formatDate(dt))
    return state
