from .config import CONFIG


def main() -> None:
    print("Maha These environment is ready.")
    print(f"Project root: {CONFIG.project_root}")
    print(f"Data dir: {CONFIG.data_dir}")
    print(f"Models dir: {CONFIG.models_dir}")


if __name__ == "__main__":
    main()
