import logging
import os
import zipfile
from io import BytesIO

logger = logging.getLogger(__name__)


def make_zipfile_bytesio(base_dir):
    zip_file = BytesIO()

    with zipfile.ZipFile(zip_file, "w",
                         compression=zipfile.ZIP_DEFLATED) as zf:
        path = os.path.normpath(base_dir)
        if path != os.curdir and path != base_dir:
            zf.write(path, os.path.relpath(path, base_dir))
            logger.info("adding '%s'", path)
        for dirpath, dirnames, filenames in os.walk(base_dir):
            for name in sorted(dirnames):
                path = os.path.normpath(os.path.join(dirpath, name))
                zf.write(path, os.path.relpath(path, base_dir))
                logger.info("adding '%s'", path)
            for name in filenames:
                path = os.path.normpath(os.path.join(dirpath, name))
                if os.path.isfile(path):
                    zf.write(path, os.path.relpath(path, base_dir))
                    logger.info("adding '%s'", path)

    return zip_file
