import os
from typing import Optional

from dotenv import load_dotenv

load_dotenv()

# Site registry
SITES = {
    "HADONG": {
        "name": "Co so Ha Noi",
        "db_url": os.getenv(
            "DB_URL_HADONG",
            "postgresql://csdlpt_user:csdlpt_password@localhost:5432/csdlpt_hadong",
        ),
    },
    "NGOCTRUC": {
        "name": "Co so Ngoc Truc",
        "db_url": os.getenv(
            "DB_URL_NGOCTRUC",
            "postgresql://csdlpt_user:csdlpt_password@localhost:5432/csdlpt_ngoctruc",
        ),
    },
    "HOALAC": {
        "name": "Co so Hoa Lac",
        "db_url": os.getenv(
            "DB_URL_HOALAC",
            "postgresql://csdlpt_user:csdlpt_password@localhost:5432/csdlpt_hoalac",
        ),
    },
}

# Shared-reference write site.
# Current split:
#   - DB logical replication: CoSo, Khoa, HocKy
#   - App replication: HocPhan
COMMON_WRITE_SITE = os.getenv("COMMON_WRITE_SITE", "HADONG")


def get_site_db_url(ma_co_so: str) -> Optional[str]:
    site = SITES.get(ma_co_so.upper())
    if site:
        return site["db_url"]
    return None


def get_site_config(ma_co_so: str) -> Optional[dict]:
    return SITES.get(ma_co_so.upper())


def get_all_sites() -> dict:
    return SITES


def get_common_write_site_db_url() -> str:
    return SITES[COMMON_WRITE_SITE]["db_url"]
