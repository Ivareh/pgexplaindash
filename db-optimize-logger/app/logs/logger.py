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


explain_logger = logging.getLogger("explain_logger")
graph_node_logger = logging.getLogger("graph_node_logger")
