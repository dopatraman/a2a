"""Hub daemon entry point."""
import uvicorn

from a2a.hub.api import create_app


def main():
    app = create_app()
    uvicorn.run(app, host="127.0.0.1", port=7800)


if __name__ == "__main__":
    main()
