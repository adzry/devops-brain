import argparse
from .orchestrator import DevOpsBrain


def main() -> None:
    parser = argparse.ArgumentParser(prog="devops-brain", description="DevOps Brain CLI")
    parser.add_argument("command", choices=["bootstrap", "import_all", "org_health"])
    args = parser.parse_args()

    brain = DevOpsBrain()

    if args.command == "bootstrap":
        brain.run_workflow("bootstrap")
    elif args.command == "import_all":
        brain.run_workflow("import_all")
    elif args.command == "org_health":
        brain.run_workflow("org_health")


if __name__ == "__main__":
    main()
