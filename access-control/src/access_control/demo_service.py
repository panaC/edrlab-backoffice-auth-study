"""Compatibility entry point for the split demo protected service package."""

from access_check_demo_service.app import DemoHandler, main

__all__ = ["DemoHandler", "main"]


if __name__ == "__main__":
    main()
