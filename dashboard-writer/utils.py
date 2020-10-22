import inputs


def write_influx(name, df):
    """Helper function to write data to InfluxDB
    """
    from influxdb_client import InfluxDBClient, Point, WriteOptions
    from influxdb_client.client.write_api import SYNCHRONOUS

    # --------------------------------------
    client = InfluxDBClient(
        url=inputs.influx_url, token=inputs.token, org=inputs.org_id, debug=False
    )

    if client.health().status == "pass":
        _write_client = client.write_api(
            write_options=WriteOptions(
                batch_size=5000,
                flush_interval=10_000,
                jitter_interval=2_000,
                retry_interval=5_000,
            )
        )

        _write_client.write(
            inputs.influx_bucket, record=df, data_frame_measurement_name=name,
        )

        print(f"- SUCCESS: {len(df.index)} records of {name} written to InfluxDB\n\n")
        _write_client.__del__()
        client.__del__()
    else:
        print("- WARNING: Unable to connect to InfluxDB - please check credentials\n\n")


def delete_influx(name):
    """Helper function to delete a 'measurement' from InfluxDB
    """
    from influxdb_client import InfluxDBClient, Point, WriteOptions
    from influxdb_client.client.write_api import SYNCHRONOUS

    client = InfluxDBClient(
        url=inputs.influx_url, token=inputs.token, org=inputs.org_id, debug=False
    )

    if client.health().status == "pass":
        start = "1970-01-01T00:00:00Z"
        stop = "2099-01-01T00:00:00Z"

        delete_api = client.delete_api()
        delete_api.delete(
            start,
            stop,
            f'_measurement="{name}"',
            bucket=inputs.influx_bucket,
            org=inputs.org_id,
        )
    else:
        print(
            "\nWARNING: Unable to connect to InfluxDB - please check your credentials\n\n"
        )


def setup_fs_s3():
    """Helper function to setup a remote S3 filesystem connection.
    """
    import s3fs

    fs = s3fs.S3FileSystem(
        key=inputs.key,
        secret=inputs.secret,
        client_kwargs={
            "endpoint_url": inputs.endpoint,
            # "verify": inputs.cert, # uncomment this when using MinIO with TLS enabled
        },
    )

    return fs


def setup_fs():
    """Helper function to setup the local file system.
    """
    from fsspec.implementations.local import LocalFileSystem
    from pathlib import Path

    fs = LocalFileSystem()

    return fs


def load_last_run(f_path):
    """Helper function for loading the date of last run (if not found, set it to 7 days ago)
    """
    from datetime import datetime, timedelta, timezone

    fmt = "%Y-%m-%d %H:%M:%S"

    try:
        with open(f_path, mode="r") as file:
            file_data = file.read()
    except:
        print(f"Warning: Unable to load file from {f_path}")

    try:
        last_run = datetime.strptime(file_data.replace("\n", ""), fmt)
        print(f"{f_path} found - loading data from {last_run}")
    except:
        last_run = datetime.utcnow() - timedelta(days=7)
        print(f"{f_path} is invalid - loading data from {last_run} (7 days ago)")

    return last_run.replace(tzinfo=timezone.utc)


def set_last_run(f_path):
    """Helper function for writing the last run date & time to local file
    """
    from datetime import datetime, timedelta, timezone

    fmt = "%Y-%m-%d %H:%M:%S"
    with open(f_path, mode="w") as file:
        file.write(datetime.utcnow().strftime(fmt))