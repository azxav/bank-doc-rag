"""Index data/samples into Qdrant. One command: python -m scripts.ingest"""

from app.core.logging import logger
from app.services.ingest import ingest_samples


def main() -> None:
    count = ingest_samples()
    logger.info("ingest_cli_done", chunks=count)
    print(f"ingested {count} chunks")


if __name__ == "__main__":
    main()
