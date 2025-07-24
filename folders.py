import os

structure = {
    ".": [
        ".env",
        "requirements.txt",
        "main.py"
    ],
    "src": {
        "__init__.py": None,
        "api": {
            "webhook_router.py": None
        },
        "services": {
            "__init__.py": None,
            "user_service.py": None,
            "project_service.py": None,
            "token_service.py": None,
            "conversation_service.py": None
        },
        "repositories": {
            "__init__.py": None,
            "postgres_repo.py": None,
            "mongodb_repo.py": None
        },
        "integrations": {
            "__init__.py": None,
            "intent_agent.py": None,
            "autodesk_api.py": None
        },
        "core": {
            "__init__.py": None,
            "schemas.py": None,
            "config.py": None,
            "cache.py": None
        },
        "utils": {
            "transformations.py": None
        }
    }
}


def create_structure(base_path, struct):
    for name, contents in struct.items():
        path = os.path.join(base_path, name)
        if isinstance(contents, dict):
            os.makedirs(path, exist_ok=True)
            create_structure(path, contents)
        elif isinstance(contents, list):
            for file in contents:
                file_path = os.path.join(base_path, file)
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                with open(file_path, "w") as f:
                    pass
        elif contents is None:
            os.makedirs(base_path, exist_ok=True)
            with open(path, "w") as f:
                pass


if __name__ == "__main__":
    create_structure(".", structure)
    print("Folder structure created.")