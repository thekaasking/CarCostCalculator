import logging.config


def setup_logging():
    print("Setting up logging...")
    # logging.basicConfig(
    #     format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    #     level=logging.DEBUG,
    #     handlers=[logging.StreamHandler(), logging.FileHandler("logs/app.log")],
    # )
    logging.config.dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "standard": {
                    "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
                }
            },
            "handlers": {
                "default": {
                    "level": "INFO",
                    "formatter": "standard",
                    "class": "logging.StreamHandler",
                },
                "file": {
                    "level": "DEBUG",
                    "formatter": "standard",
                    "class": "logging.FileHandler",
                    "filename": "logs/app.log",
                    "mode": "w",
                },
            },
            "loggers": {
                "": {"handlers": ["default"], "level": "INFO", "propagate": True}
            },
        }
    )


setup_logging()
