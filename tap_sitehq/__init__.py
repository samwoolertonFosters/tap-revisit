import os
import json
import asyncio
import aiohttp
import singer
from singer import metadata

from tap_sitehq.utility import get_abs_path, RateLimiter
from tap_sitehq.fetch import write_bookmark, handle_resource

logger = singer.get_logger()

REQUIRED_CONFIG_KEYS = ["api_key"]


def load_schemas():
    schemas = {}

    for filename in os.listdir(get_abs_path("schemas")):
        path = get_abs_path("schemas") + "/" + filename
        file_raw = filename.replace(".json", "")
        with open(path) as file:
            schemas[file_raw] = json.load(file)

    return schemas


def populate_metadata(schema_name, schema):
    mdata = metadata.new()
    mdata = metadata.write(mdata, (), "table-key-properties", ["id"])

    for field_name in schema["properties"].keys():
        mdata = metadata.write(
            mdata,
            ("properties", field_name),
            "inclusion",
            "automatic" if field_name == "id" else "available",
        )

    return mdata


def get_catalog():
    raw_schemas = load_schemas()
    streams = []

    for schema_name, schema in raw_schemas.items():

        # get metadata for each field
        mdata = populate_metadata(schema_name, schema)

        # create and add catalog entry
        catalog_entry = {
            "stream": schema_name,
            "tap_stream_id": schema_name,
            "schema": schema,
            "metadata": metadata.to_list(mdata),
            "key_properties": ["id"],
        }
        streams.append(catalog_entry)

    return {"streams": streams}


def do_discover():
    catalog = get_catalog()
    # dump catalog
    print(json.dumps(catalog, indent=2))


def get_selected_streams(catalog):
    """
    Gets selected streams.  Checks schema's 'selected'
    first -- and then checks metadata, looking for an empty
    breadcrumb and mdata with a 'selected' entry
    """
    selected_streams = []
    for stream in catalog["streams"]:
        stream_metadata = stream["metadata"]
        if stream["schema"].get("selected", False):
            selected_streams.append(stream["tap_stream_id"])
        else:
            for entry in stream_metadata:
                # stream metadata will have empty breadcrumb
                if not entry["breadcrumb"] and entry["metadata"].get("selected", None):
                    selected_streams.append(stream["tap_stream_id"])

    return selected_streams


def get_stream_from_catalog(stream_id, catalog):
    for stream in catalog["streams"]:
        if stream["tap_stream_id"] == stream_id:
            return stream
    return None


async def do_sync(session, state, catalog, selected_stream_ids):
    streams_to_sync = [
        stream
        for stream in catalog["streams"]
        if stream["tap_stream_id"] in selected_stream_ids
    ]

    streams_futures = []

    for stream in streams_to_sync:
        stream_id = stream["tap_stream_id"]
        stream_schema = stream["schema"]
        mdata = stream["metadata"]

        singer.write_schema(stream_id, stream_schema, stream["key_properties"])

        schemas = {stream_id: stream_schema}

        streams_futures.append(
            handle_resource(session, stream_id, schemas, state, mdata)
        )

    streams_resolved = await asyncio.gather(*streams_futures)

    # update bookmark by merging in all streams
    for (resource, extraction_time) in streams_resolved:
        state = write_bookmark(state, resource, extraction_time)
    singer.write_state(state)


async def run_async(config, state, catalog):
    selected_stream_ids = get_selected_streams(catalog)

    headers = {"Authorization": "Token " + config["api_key"]}
    async with aiohttp.ClientSession(headers=headers) as session:
        session = RateLimiter(session)
        await do_sync(session, state, catalog, selected_stream_ids)


@singer.utils.handle_top_exception(logger)
def main():
    args = singer.utils.parse_args(REQUIRED_CONFIG_KEYS)

    if args.discover:
        do_discover()
    else:
        catalog = args.properties if args.properties else get_catalog()
        asyncio.get_event_loop().run_until_complete(
            run_async(args.config, args.state, catalog)
        )


if __name__ == "__main__":
    main()
