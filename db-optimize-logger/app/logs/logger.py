import logging
import logging.config
from pathlib import Path

import yaml


def setup_logging():
    # Determine the path to config.yml relative to the current directory
    config_path = Path(__file__).parent / "config" / "config.yml"

    # Load YAML configuration
    with open(config_path) as f_in:
        config = yaml.safe_load(f_in)

    # Apply logging configuration
    logging.config.dictConfig(config)


app_logger = logging.getLogger("app_logger")  # For general app use

explain_logger = logging.getLogger(
    "explain_logger"
)  # Logs for explain analyze information

db_logger = logging.getLogger("db_logger")  # Log database information

graph_node_logger = logging.getLogger("graph_node_logger")  # Log graph node information
