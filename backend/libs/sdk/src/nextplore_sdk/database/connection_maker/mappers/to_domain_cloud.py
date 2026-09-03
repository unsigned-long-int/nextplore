
from nextplore_sdk.database.connection_maker.exc.exceptions import MissingCloud
from nextplore_sdk.database.connection_maker.models.cloud import Cloud

CLOUD_MAP: dict[str, Cloud] = {
    "aws": Cloud.AWS,
    "azure": Cloud.AZURE,
    "gcp": Cloud.GCP,
    "snowflake_managed": Cloud.SNOWFLAKE_MANAGED,
}


def to_domain_cloud(cloud: str) -> Cloud:
    try:
        return CLOUD_MAP[cloud]
    except KeyError:
        raise MissingCloud(f"Cloud not found in map: {cloud}")
